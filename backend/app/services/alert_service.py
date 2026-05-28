from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.monitoring import IncidentReport, MonitoringLog, SystemAlert

INCIDENT_THRESHOLD = 3


def check_alert_rules(metrics: dict) -> list[dict]:
    """Pure function: returns list of triggered rule dicts given a metrics snapshot."""
    now = datetime.now(timezone.utc)
    triggered = []

    if metrics.get("error_rate_percent", 0) > 10:
        triggered.append({
            "alert_type": "high_error_rate",
            "severity": "high",
            "title": "High API error rate detected",
            "description": f"Error rate is {metrics['error_rate_percent']:.1f}% (threshold: 10%)",
            "affected_service": "api",
            "recommended_action": "Check recent deployments, database connections, and error logs.",
            "business_impact": "Users may be experiencing failures when accessing the platform.",
        })

    if metrics.get("avg_response_time_ms", 0) > 3000:
        triggered.append({
            "alert_type": "slow_response_time",
            "severity": "medium",
            "title": "API response time exceeds 3000ms",
            "description": f"Average response time is {metrics['avg_response_time_ms']:.0f}ms",
            "affected_service": "api",
            "recommended_action": "Review database query performance and server load.",
            "business_impact": "Users are experiencing slow responses when using the platform.",
        })

    if metrics.get("failed_login_events", 0) > 20:
        triggered.append({
            "alert_type": "high_failed_logins",
            "severity": "high",
            "title": "High number of failed login attempts — possible brute force",
            "description": f"Failed logins: {metrics['failed_login_events']} in last 10 minutes",
            "affected_service": "auth",
            "recommended_action": "Review failed login sources. Consider blocking suspicious IPs.",
            "business_impact": "Possible unauthorized access attempt. Account lockouts may affect legitimate users.",
        })

    if metrics.get("failed_document_ingestion", 0) >= 3:
        triggered.append({
            "alert_type": "failed_document_ingestion",
            "severity": "medium",
            "title": "Multiple document ingestion failures",
            "description": f"{metrics['failed_document_ingestion']} documents failed to process",
            "affected_service": "document_pipeline",
            "recommended_action": "Check document processing worker logs and file validation service.",
            "business_impact": "Documents are not being indexed and are unavailable for AI search.",
        })

    if metrics.get("failed_ai_calls", 0) >= 5:
        triggered.append({
            "alert_type": "ai_service_failure",
            "severity": "critical",
            "title": "Cerebras AI service failures detected",
            "description": f"{metrics['failed_ai_calls']} AI API calls failed",
            "affected_service": "cerebras_llm",
            "recommended_action": "Verify CEREBRAS_API_KEY is valid and service is reachable.",
            "business_impact": "AI chat and knowledge retrieval are unavailable for all users.",
        })

    if metrics.get("avg_hallucination_risk", 0) > 0.6:
        triggered.append({
            "alert_type": "high_hallucination_risk",
            "severity": "high",
            "title": "High AI hallucination risk trend",
            "description": f"Average hallucination risk is {metrics['avg_hallucination_risk']:.2f}",
            "affected_service": "rag_pipeline",
            "recommended_action": "Review document quality and re-index problematic documents.",
            "business_impact": "AI responses may contain unreliable information.",
        })

    if metrics.get("active_users", -1) == 0 and metrics.get("expected_active", True):
        triggered.append({
            "alert_type": "no_active_users",
            "severity": "low",
            "title": "No active users detected during business hours",
            "description": "Active user count dropped to 0",
            "affected_service": "api",
            "recommended_action": "Verify API accessibility and check for network/DNS issues.",
            "business_impact": "Platform may be inaccessible to users.",
        })

    if metrics.get("slow_query_count", 0) > 50:
        triggered.append({
            "alert_type": "database_slow_queries",
            "severity": "medium",
            "title": "High number of slow database queries",
            "description": f"{metrics['slow_query_count']} queries exceeded 1000ms in last hour",
            "affected_service": "database",
            "recommended_action": "Review database indexes and query optimization. Consider connection pool settings.",
            "business_impact": "Slow database queries are degrading application performance.",
        })

    return triggered


async def create_alert(
    db: AsyncSession,
    organization_id: UUID,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
    affected_service: str,
    recommended_action: str | None = None,
    business_impact: str | None = None,
) -> SystemAlert:
    existing = await db.execute(
        select(SystemAlert).where(
            SystemAlert.organization_id == organization_id,
            SystemAlert.alert_type == alert_type,
            SystemAlert.status.in_(["open", "investigating"]),
        )
    )
    if existing.scalar_one_or_none() is not None:
        return None

    alert = SystemAlert(
        organization_id=organization_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        affected_service=affected_service,
        recommended_action=recommended_action,
        business_impact=business_impact,
    )
    db.add(alert)
    await db.flush()
    return alert


async def group_into_incident(
    db: AsyncSession,
    organization_id: UUID,
    alert_type: str,
    alert: SystemAlert,
) -> IncidentReport | None:
    count_result = await db.execute(
        select(func.count()).where(
            SystemAlert.organization_id == organization_id,
            SystemAlert.alert_type == alert_type,
        )
    )
    alert_count = int(count_result.scalar_one() or 0)

    if alert_count < INCIDENT_THRESHOLD:
        return None

    existing = await db.execute(
        select(IncidentReport).where(
            IncidentReport.organization_id == organization_id,
            IncidentReport.title.contains(alert_type),
            IncidentReport.status == "open",
        )
    )
    incident = existing.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if incident:
        incident.error_count += 1
        incident.last_occurrence = now
    else:
        incident = IncidentReport(
            organization_id=organization_id,
            title=f"Recurring incident: {alert.title}",
            description=f"Alert type '{alert_type}' has triggered {alert_count} times.",
            severity=alert.severity,
            status="open",
            affected_services={"alert_type": alert_type, "service": alert.affected_service},
            error_count=alert_count,
            first_occurrence=now,
            last_occurrence=now,
            business_impact=alert.business_impact,
        )
        db.add(incident)

    await db.flush()
    return incident


async def check_and_create_alerts(db: AsyncSession, organization_id: UUID) -> list[SystemAlert]:
    from app.services.monitoring_service import get_system_metrics, get_database_performance_metrics

    metrics = await get_system_metrics(db, organization_id, period="1h")
    db_metrics = await get_database_performance_metrics(db, organization_id)
    metrics.update(db_metrics)

    ai_trend = await db.execute(
        select(func.avg(MonitoringLog.response_time_ms)).where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.event_type == "ai_query",
            MonitoringLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=1),
        )
    )
    triggered_rules = check_alert_rules(metrics)

    created: list[SystemAlert] = []
    for rule in triggered_rules:
        alert = await create_alert(
            db=db,
            organization_id=organization_id,
            alert_type=rule["alert_type"],
            severity=rule["severity"],
            title=rule["title"],
            description=rule["description"],
            affected_service=rule["affected_service"],
            recommended_action=rule.get("recommended_action"),
            business_impact=rule.get("business_impact"),
        )
        if alert is not None:
            created.append(alert)
            await group_into_incident(db, organization_id, rule["alert_type"], alert)

    return created


async def get_active_alerts(
    db: AsyncSession, organization_id: UUID
) -> list[SystemAlert]:
    result = await db.execute(
        select(SystemAlert)
        .where(
            SystemAlert.organization_id == organization_id,
            SystemAlert.status.in_(["open", "investigating"]),
        )
        .order_by(SystemAlert.severity, SystemAlert.created_at.desc())
    )
    return list(result.scalars().all())


async def update_alert_status(
    db: AsyncSession,
    alert_id: UUID,
    organization_id: UUID,
    new_status: str,
    updated_by: UUID,
    resolution_notes: str | None = None,
) -> SystemAlert | None:
    result = await db.execute(
        select(SystemAlert).where(
            SystemAlert.id == alert_id,
            SystemAlert.organization_id == organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        return None

    alert.status = new_status
    if new_status == "resolved":
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = updated_by

    db.add(
        AuditLog(
            organization_id=organization_id,
            user_id=updated_by,
            action="ALERT_STATUS_UPDATED",
            resource_type="system_alert",
            resource_id=str(alert.id),
            new_value={"status": new_status, "resolution_notes": resolution_notes},
        )
    )
    await db.flush()
    return alert
