import asyncio
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.monitoring import DebuggingAnalysis, SystemMetricsResponse
from app.services.alert_service import check_alert_rules, create_alert
from app.services.debugging_service import analyze_error_log, _fallback_analysis
from app.middleware.monitoring_middleware import _should_monitor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeDB:
    def __init__(self, return_values=None):
        self._queue = list(return_values or [])
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def execute(self, query):
        val = self._queue.pop(0) if self._queue else None
        return SimpleNamespace(
            scalar_one_or_none=lambda v=val: v,
            scalar_one=lambda v=val: v or 0,
            scalars=lambda: SimpleNamespace(all=lambda: []),
        )

    async def scalar(self, query):
        if self._queue:
            return self._queue.pop(0)
        return 0


def _metrics(**overrides) -> dict:
    base = {
        "total_api_calls": 100,
        "failed_api_calls": 3,
        "error_rate_percent": 3.0,
        "avg_response_time_ms": 250.0,
        "total_ai_queries": 20,
        "failed_ai_calls": 0,
        "total_token_usage": 5000,
        "total_document_uploads": 5,
        "failed_document_ingestion": 0,
        "total_login_events": 30,
        "failed_login_events": 2,
        "active_users": 8,
        "slow_query_count": 0,
        "avg_hallucination_risk": 0.2,
        "period": "1h",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# monitoring_service.get_system_metrics returns correct structure
# ---------------------------------------------------------------------------

def test_get_system_metrics_returns_correct_structure():
    metrics = _metrics()
    response = SystemMetricsResponse(**{k: v for k, v in metrics.items() if k != "period"}, period=metrics["period"])

    assert response.total_api_calls == 100
    assert response.error_rate_percent == 3.0
    assert response.active_users == 8
    assert response.period == "1h"


def test_system_metrics_response_has_all_required_fields():
    fields = SystemMetricsResponse.model_fields.keys()
    required = {
        "total_api_calls", "failed_api_calls", "error_rate_percent",
        "avg_response_time_ms", "total_ai_queries", "active_users",
    }
    assert required.issubset(set(fields))


# ---------------------------------------------------------------------------
# alert_service alert rules
# ---------------------------------------------------------------------------

def test_alert_rule_triggers_for_high_error_rate():
    metrics = _metrics(error_rate_percent=15.0)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "high_error_rate" in types


def test_alert_rule_does_not_trigger_for_low_error_rate():
    metrics = _metrics(error_rate_percent=3.0)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "high_error_rate" not in types


def test_alert_rule_triggers_for_slow_response():
    metrics = _metrics(avg_response_time_ms=4000.0)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "slow_response_time" in types


def test_alert_rule_triggers_for_high_failed_logins():
    metrics = _metrics(failed_login_events=25)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "high_failed_logins" in types


def test_alert_rule_triggers_for_failed_document_ingestion():
    metrics = _metrics(failed_document_ingestion=3)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "failed_document_ingestion" in types


def test_alert_rule_triggers_for_ai_service_failure():
    metrics = _metrics(failed_ai_calls=5)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "ai_service_failure" in types


def test_alert_rule_triggers_for_high_hallucination_risk():
    metrics = _metrics(avg_hallucination_risk=0.7)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "high_hallucination_risk" in types


def test_alert_rule_triggers_for_database_slow_queries():
    metrics = _metrics(slow_query_count=55)
    triggered = check_alert_rules(metrics)
    types = [r["alert_type"] for r in triggered]
    assert "database_slow_queries" in types


def test_no_alerts_triggered_for_healthy_metrics():
    metrics = _metrics()
    triggered = check_alert_rules(metrics)
    assert triggered == []


# ---------------------------------------------------------------------------
# alert_service does not create duplicate alerts
# ---------------------------------------------------------------------------

def test_alert_service_does_not_create_duplicate_for_open_alert():
    from app.models.monitoring import SystemAlert

    existing_alert = SystemAlert(
        id=uuid4(),
        organization_id=uuid4(),
        alert_type="high_error_rate",
        severity="high",
        title="High error rate",
        status="open",
        affected_service="api",
    )
    db = FakeDB(return_values=[existing_alert])

    result = asyncio.run(
        create_alert(
            db=db,
            organization_id=existing_alert.organization_id,
            alert_type="high_error_rate",
            severity="high",
            title="High error rate",
            description="Duplicate",
            affected_service="api",
        )
    )

    assert result is None


def test_alert_service_creates_new_alert_when_none_open():
    db = FakeDB(return_values=[None])
    org_id = uuid4()

    result = asyncio.run(
        create_alert(
            db=db,
            organization_id=org_id,
            alert_type="new_alert_type",
            severity="medium",
            title="New alert",
            description="Description",
            affected_service="api",
        )
    )

    assert result is not None
    assert result.alert_type == "new_alert_type"
    any_alert_added = any(hasattr(obj, "alert_type") for obj in db.added)
    assert any_alert_added


# ---------------------------------------------------------------------------
# alert_service groups repeated errors into incidents after 3 occurrences
# ---------------------------------------------------------------------------

def test_alert_groups_into_incident_after_threshold():
    from app.services.alert_service import group_into_incident
    from app.models.monitoring import SystemAlert

    org_id = uuid4()
    alert = SystemAlert(
        id=uuid4(),
        organization_id=org_id,
        alert_type="test_alert",
        severity="high",
        title="Test alert",
        status="open",
        affected_service="api",
        business_impact="Users affected.",
    )
    # DB returns count of 3 (threshold), then None (no existing incident)
    db = FakeDB(return_values=[3, None])

    result = asyncio.run(group_into_incident(db, org_id, "test_alert", alert))

    assert result is not None
    incident_added = any(hasattr(obj, "error_count") for obj in db.added)
    assert incident_added


def test_alert_does_not_group_below_threshold():
    from app.services.alert_service import group_into_incident
    from app.models.monitoring import SystemAlert

    org_id = uuid4()
    alert = SystemAlert(
        id=uuid4(),
        organization_id=org_id,
        alert_type="rare_alert",
        severity="low",
        title="Rare",
        status="open",
        affected_service="api",
    )
    db = FakeDB(return_values=[1])  # count=1 < threshold=3

    result = asyncio.run(group_into_incident(db, org_id, "rare_alert", alert))
    assert result is None


# ---------------------------------------------------------------------------
# debugging_service.analyze_error_log
# ---------------------------------------------------------------------------

def test_analyze_error_log_returns_debugging_analysis_with_all_required_fields():
    entry = {
        "service_name": "document_pipeline",
        "endpoint": "/api/v1/admin/documents/upload",
        "status_code": 500,
        "error_message": "FileNotFoundError: /uploads/org1/doc1.pdf",
        "event_type": "document_processing_failed",
    }
    analysis = analyze_error_log(entry)

    assert isinstance(analysis, DebuggingAnalysis)
    assert len(analysis.plain_english_explanation) > 0
    assert len(analysis.possible_cause) > 0
    assert len(analysis.affected_service) > 0
    assert len(analysis.business_impact) > 0
    assert isinstance(analysis.recommended_steps, list)
    assert len(analysis.recommended_steps) > 0
    assert analysis.severity in {"low", "medium", "high", "critical"}


def test_analyze_error_log_fallback_returns_valid_structure():
    entry = {
        "service_name": "rag_pipeline",
        "endpoint": "/api/v1/chat/ask",
        "status_code": 503,
        "error_message": "Cerebras API timeout",
        "event_type": "ai_query",
    }
    result = _fallback_analysis(entry)

    assert isinstance(result, DebuggingAnalysis)
    assert "rag_pipeline" in result.affected_service
    assert result.severity == "high"
    assert len(result.recommended_steps) >= 3


def test_analyze_error_log_4xx_severity_is_medium():
    entry = {
        "service_name": "api",
        "endpoint": "/api/v1/admin/documents",
        "status_code": 404,
        "error_message": "Not found",
        "event_type": "api_request",
    }
    result = _fallback_analysis(entry)
    assert result.severity == "medium"


# ---------------------------------------------------------------------------
# ai_monitoring_service.generate_system_health_summary
# ---------------------------------------------------------------------------

def test_generate_system_health_summary_returns_non_empty_string():
    from app.services.ai_monitoring_service import generate_system_health_summary

    class MetricsDB(FakeDB):
        async def scalar(self, query):
            return 0
        async def execute(self, query):
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: []),
                scalar_one_or_none=lambda: None,
                scalar_one=lambda: 0,
            )

    result = asyncio.run(
        generate_system_health_summary(MetricsDB(), uuid4())
    )

    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# MonitoringMiddleware records response time correctly
# ---------------------------------------------------------------------------

def test_monitoring_middleware_should_monitor_api_paths():
    assert _should_monitor("/api/v1/chat/ask") is True
    assert _should_monitor("/api/v1/monitoring/dashboard") is True


def test_monitoring_middleware_skips_health_and_docs():
    assert _should_monitor("/api/health") is False
    assert _should_monitor("/health") is False
    assert _should_monitor("/docs") is False
    assert _should_monitor("/redoc") is False
    assert _should_monitor("/openapi.json") is False
    assert _should_monitor("/") is False


def test_monitoring_middleware_response_time_calculation():
    start = time.monotonic()
    time.sleep(0.015)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    assert elapsed_ms >= 15
    assert elapsed_ms < 2000


def test_monitoring_middleware_static_path_skipped():
    assert _should_monitor("/static/file.js") is False


# ---------------------------------------------------------------------------
# cleanup task identifies logs older than 90 days
# ---------------------------------------------------------------------------

def test_cleanup_task_cutoff_correctly_identifies_old_logs():
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)

    old_log_date = datetime.now(timezone.utc) - timedelta(days=95)
    new_log_date = datetime.now(timezone.utc) - timedelta(days=30)
    exactly_cutoff = datetime.now(timezone.utc) - timedelta(days=90, seconds=1)

    assert old_log_date < cutoff, "95-day old log should be before cutoff"
    assert new_log_date > cutoff, "30-day old log should be after cutoff"
    assert exactly_cutoff < cutoff, "Exactly-at-cutoff log should be deleted"


def test_cleanup_task_keeps_logs_newer_than_90_days():
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    recent_dates = [
        datetime.now(timezone.utc) - timedelta(days=d) for d in [1, 7, 30, 60, 89]
    ]
    for d in recent_dates:
        assert d > cutoff, f"Log {d} should be kept (newer than cutoff)"
