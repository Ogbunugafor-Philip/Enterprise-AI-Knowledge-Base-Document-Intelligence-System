from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.cache_config import CacheManager, TTL_MONITORING_METRICS, get_redis_client, make_cache_key
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.monitoring import IncidentReport, SystemAlert
from app.models.user import User
from app.schemas.monitoring import (
    AITrustReport,
    AlertResponse,
    AlertUpdateRequest,
    IncidentResponse,
    MonitoringDashboardData,
    SystemHealthSummary,
    SystemMetricsResponse,
)
from app.services import (
    ai_monitoring_service,
    alert_service,
    debugging_service,
    monitoring_service,
    rag_logging_service,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

_ADMIN_DEP = Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))


def _alert_resp(alert: SystemAlert) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        description=alert.description,
        affected_service=alert.affected_service,
        status=alert.status,
        recommended_action=alert.recommended_action,
        business_impact=alert.business_impact,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def _incident_resp(inc: IncidentReport) -> IncidentResponse:
    return IncidentResponse(
        id=inc.id,
        title=inc.title,
        description=inc.description,
        severity=inc.severity,
        status=inc.status,
        affected_services=inc.affected_services,
        error_count=inc.error_count,
        first_occurrence=inc.first_occurrence,
        last_occurrence=inc.last_occurrence,
        root_cause=inc.root_cause,
        resolution_steps=inc.resolution_steps,
        business_impact=inc.business_impact,
    )


@router.get("/dashboard", response_model=MonitoringDashboardData, dependencies=[_ADMIN_DEP])
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MonitoringDashboardData:
    org_id = current_user.organization_id
    metrics_dict = await monitoring_service.get_system_metrics(db, org_id)
    alerts = await alert_service.get_active_alerts(db, org_id)
    rt_trend = await monitoring_service.get_response_time_trend(db, org_id)
    err_trend = await monitoring_service.get_error_trend(db, org_id)
    ai_trend = await monitoring_service.get_ai_quality_trend(db, org_id)
    top_ep = await monitoring_service.get_top_endpoints(db, org_id)

    try:
        health_text = await ai_monitoring_service.generate_system_health_summary(db, org_id)
        risk_data = await ai_monitoring_service.analyze_system_risk(db, org_id)
        risk_level = risk_data.get("overall_risk_level", "low")
    except Exception:
        health_text = "Monitoring data is available."
        risk_level = "low"

    return MonitoringDashboardData(
        system_metrics=SystemMetricsResponse(**metrics_dict),
        active_alerts=[_alert_resp(a) for a in alerts],
        health_summary=SystemHealthSummary(
            summary_text=health_text,
            risk_level=risk_level,
            generated_at=datetime.now(timezone.utc),
        ),
        ai_quality_trend=ai_trend,
        response_time_trend=rt_trend,
        error_trend=err_trend,
        top_endpoints=top_ep,
    )


@router.get("/metrics", response_model=SystemMetricsResponse, dependencies=[_ADMIN_DEP])
async def get_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    time_period: str = Query(default="24h", pattern="^(1h|6h|24h|7d|30d)$"),
    redis=Depends(get_redis_client),
) -> SystemMetricsResponse:
    cache_key = make_cache_key("monitoring_metrics", str(current_user.organization_id), time_period)
    if redis:
        cached = await CacheManager(redis).get_cached_response(cache_key)
        if cached:
            return SystemMetricsResponse(**cached)
    metrics = await monitoring_service.get_system_metrics(
        db, current_user.organization_id, period=time_period
    )
    result = SystemMetricsResponse(**metrics)
    if redis:
        await CacheManager(redis).cache_response(cache_key, result.model_dump(), TTL_MONITORING_METRICS)
    return result


@router.get("/alerts", response_model=list[AlertResponse], dependencies=[_ADMIN_DEP])
async def list_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    severity: str | None = Query(default=None),
) -> list[AlertResponse]:
    alerts = await alert_service.get_active_alerts(db, current_user.organization_id)
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    return [_alert_resp(a) for a in alerts]


@router.get("/alerts/{alert_id}", dependencies=[_ADMIN_DEP])
async def get_alert(
    alert_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    result = await db.execute(
        select(SystemAlert).where(
            SystemAlert.id == alert_id,
            SystemAlert.organization_id == current_user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    entry = {
        "service_name": alert.affected_service or "unknown",
        "endpoint": None,
        "status_code": 500,
        "error_message": alert.description,
        "event_type": alert.alert_type,
    }
    analysis = debugging_service.analyze_error_log(entry)

    return {
        "alert": _alert_resp(alert).model_dump(),
        "debugging_analysis": analysis.model_dump(),
    }


@router.put("/alerts/{alert_id}/status", dependencies=[_ADMIN_DEP])
async def update_alert(
    alert_id: UUID,
    payload: AlertUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> AlertResponse:
    alert = await alert_service.update_alert_status(
        db, alert_id, current_user.organization_id, payload.status, current_user.id, payload.resolution_notes
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await db.commit()
    await db.refresh(alert)
    return _alert_resp(alert)


@router.get("/incidents", response_model=list[IncidentResponse], dependencies=[_ADMIN_DEP])
async def list_incidents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[IncidentResponse]:
    query = select(IncidentReport).where(IncidentReport.organization_id == current_user.organization_id)
    if status_filter:
        query = query.where(IncidentReport.status == status_filter)
    result = await db.execute(query.order_by(IncidentReport.created_at.desc()))
    return [_incident_resp(inc) for inc in result.scalars().all()]


@router.get("/incidents/{incident_id}", dependencies=[_ADMIN_DEP])
async def get_incident(
    incident_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    result = await db.execute(
        select(IncidentReport).where(
            IncidentReport.id == incident_id,
            IncidentReport.organization_id == current_user.organization_id,
        )
    )
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    summary = await debugging_service.generate_incident_summary(
        db, incident_id, current_user.organization_id
    )
    return {"incident": _incident_resp(inc).model_dump(), "ai_summary": summary}


@router.get("/health-summary", dependencies=[_ADMIN_DEP])
async def health_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> SystemHealthSummary:
    text = await ai_monitoring_service.generate_system_health_summary(db, current_user.organization_id)
    risk_data = await ai_monitoring_service.analyze_system_risk(db, current_user.organization_id)
    return SystemHealthSummary(
        summary_text=text,
        risk_level=risk_data.get("overall_risk_level", "low"),
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/risk-analysis", dependencies=[_ADMIN_DEP])
async def risk_analysis(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    return await ai_monitoring_service.analyze_system_risk(db, current_user.organization_id)


@router.get("/ai-trust-report", dependencies=[_ADMIN_DEP])
async def ai_trust_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> AITrustReport:
    analytics = await rag_logging_service.get_ai_quality_analytics(db, current_user.organization_id)
    report_text = await ai_monitoring_service.generate_ai_trust_report(db, current_user.organization_id)

    total = analytics.get("total_queries", 0)
    rejected = analytics.get("total_rejected", 0)
    avg_conf = analytics.get("avg_retrieval_confidence", 0.0)
    avg_risk = analytics.get("avg_hallucination_risk", 0.0)
    rejection_rate = round(rejected / total * 100, 1) if total > 0 else 0.0

    if avg_conf >= 0.8 and avg_risk <= 0.2:
        trust_level = "high"
    elif avg_conf >= 0.6 and avg_risk <= 0.4:
        trust_level = "medium"
    else:
        trust_level = "low"

    return AITrustReport(
        avg_confidence_score=avg_conf,
        avg_hallucination_risk=avg_risk,
        total_responses=total,
        rejected_responses=rejected,
        rejection_rate_percent=rejection_rate,
        problematic_documents=[],
        trust_level=trust_level,
        report_text=report_text,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/debugging/history", dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def debugging_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    severity: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return await debugging_service.get_debugging_history(
        db, current_user.organization_id, severity=severity, page=page, page_size=page_size
    )


@router.get("/ai-quality", dependencies=[_ADMIN_DEP])
async def ai_quality(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    return await rag_logging_service.get_ai_quality_analytics(
        db, current_user.organization_id, days=days
    )
