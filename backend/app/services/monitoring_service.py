from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import MonitoringLog

_SKIP_PATHS = {"/api/health", "/health", "/docs", "/redoc", "/openapi.json", "/"}

_PERIOD_MAP = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _since(period: str) -> datetime:
    delta = _PERIOD_MAP.get(period, timedelta(hours=24))
    return datetime.now(timezone.utc) - delta


async def track_api_request(
    db: AsyncSession,
    *,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
    user_id: UUID | None,
    organization_id: UUID | None,
    ip_address: str | None,
) -> None:
    if any(endpoint.startswith(skip) for skip in _SKIP_PATHS):
        return
    if organization_id is None:
        return
    db.add(
        MonitoringLog(
            organization_id=organization_id,
            event_type="api_request",
            service_name="api",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            ip_address=ip_address,
        )
    )
    await db.flush()


async def track_ai_query(
    db: AsyncSession,
    *,
    user_id: UUID,
    organization_id: UUID,
    response_time_ms: int,
    token_usage: dict,
    response_rejected: bool,
) -> None:
    db.add(
        MonitoringLog(
            organization_id=organization_id,
            event_type="ai_query",
            service_name="rag_pipeline",
            endpoint="/api/v1/chat/ask",
            method="POST",
            status_code=200 if not response_rejected else 206,
            response_time_ms=response_time_ms,
            user_id=user_id,
            token_usage=token_usage,
        )
    )
    await db.flush()


async def track_document_event(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID | None,
    event_type: str,
    document_id: str | None = None,
    file_name: str | None = None,
    error_message: str | None = None,
) -> None:
    db.add(
        MonitoringLog(
            organization_id=organization_id,
            event_type=event_type,
            service_name="document_pipeline",
            endpoint=f"/api/v1/admin/documents/{document_id}" if document_id else None,
            status_code=500 if "failed" in event_type else 200,
            user_id=user_id,
            error_message=error_message,
            token_usage={"document_id": document_id, "file_name": file_name} if document_id else None,
        )
    )
    await db.flush()


async def track_auth_event(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    user_id: UUID | None,
    event_type: str,
    ip_address: str | None = None,
) -> None:
    if organization_id is None:
        return
    db.add(
        MonitoringLog(
            organization_id=organization_id,
            event_type=event_type,
            service_name="auth",
            endpoint="/api/v1/auth/login",
            method="POST",
            status_code=200 if "success" in event_type else 401,
            user_id=user_id,
            ip_address=ip_address,
        )
    )
    await db.flush()


async def get_active_users(db: AsyncSession, organization_id: UUID) -> int:
    since = datetime.now(timezone.utc) - timedelta(minutes=15)
    result = await db.execute(
        select(func.count(distinct(MonitoringLog.user_id))).where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.created_at >= since,
            MonitoringLog.user_id.isnot(None),
        )
    )
    return int(result.scalar_one() or 0)


async def get_system_metrics(
    db: AsyncSession,
    organization_id: UUID,
    period: str = "24h",
) -> dict:
    since = _since(period)
    base = and_(
        MonitoringLog.organization_id == organization_id,
        MonitoringLog.created_at >= since,
    )

    async def count(extra_filter=None):
        q = select(func.count()).where(base)
        if extra_filter is not None:
            q = q.where(extra_filter)
        return int((await db.scalar(q)) or 0)

    async def avg_val(col, extra_filter=None):
        q = select(func.avg(col)).where(base)
        if extra_filter is not None:
            q = q.where(extra_filter)
        val = await db.scalar(q)
        return float(val) if val is not None else 0.0

    async def sum_val(col, extra_filter=None):
        q = select(func.coalesce(func.sum(col), 0)).where(base)
        if extra_filter is not None:
            q = q.where(extra_filter)
        return int((await db.scalar(q)) or 0)

    total_api = await count(MonitoringLog.event_type == "api_request")
    failed_api = await count(
        and_(MonitoringLog.event_type == "api_request", MonitoringLog.status_code >= 400)
    )
    avg_rt = await avg_val(
        MonitoringLog.response_time_ms, MonitoringLog.event_type == "api_request"
    )
    total_ai = await count(MonitoringLog.event_type == "ai_query")
    failed_ai = await count(
        and_(MonitoringLog.event_type == "ai_query", MonitoringLog.status_code >= 400)
    )
    total_doc = await count(MonitoringLog.event_type == "document_upload")
    failed_doc = await count(MonitoringLog.event_type == "document_processing_failed")
    login_total = await count(MonitoringLog.event_type.in_(["login_success", "login_failed"]))
    login_failed = await count(MonitoringLog.event_type == "login_failed")
    active = await get_active_users(db, organization_id)

    error_rate = round((failed_api / total_api * 100), 1) if total_api > 0 else 0.0

    return {
        "total_api_calls": total_api,
        "failed_api_calls": failed_api,
        "error_rate_percent": error_rate,
        "avg_response_time_ms": round(avg_rt, 1),
        "total_ai_queries": total_ai,
        "failed_ai_calls": failed_ai,
        "total_token_usage": 0,
        "total_document_uploads": total_doc,
        "failed_document_ingestion": failed_doc,
        "total_login_events": login_total,
        "failed_login_events": login_failed,
        "active_users": active,
        "period": period,
    }


async def get_response_time_trend(
    db: AsyncSession, organization_id: UUID
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(
            func.date_trunc("hour", MonitoringLog.created_at).label("hour"),
            func.avg(MonitoringLog.response_time_ms).label("avg_rt"),
        )
        .where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.event_type == "api_request",
            MonitoringLog.created_at >= since,
            MonitoringLog.response_time_ms.isnot(None),
        )
        .group_by("hour")
        .order_by("hour")
    )
    rows = result.all()
    return [
        {
            "timestamp": row[0].isoformat() if row[0] else "",
            "avg_response_time_ms": round(float(row[1]), 1) if row[1] else 0.0,
        }
        for row in rows
    ]


async def get_error_trend(
    db: AsyncSession, organization_id: UUID
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(
            func.date_trunc("hour", MonitoringLog.created_at).label("hour"),
            func.count().label("error_count"),
        )
        .where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.status_code >= 400,
            MonitoringLog.created_at >= since,
        )
        .group_by("hour")
        .order_by("hour")
    )
    rows = result.all()
    return [
        {"timestamp": row[0].isoformat() if row[0] else "", "error_count": int(row[1]), "endpoint": None}
        for row in rows
    ]


async def get_ai_quality_trend(
    db: AsyncSession, organization_id: UUID
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(MonitoringLog)
        .where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.event_type == "ai_query",
            MonitoringLog.created_at >= since,
            MonitoringLog.token_usage.isnot(None),
        )
        .order_by(MonitoringLog.created_at)
    )
    logs = list(result.scalars().all())
    daily: dict[str, dict] = {}
    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"conf": [], "risk": [], "rejected": 0}
        tu = log.token_usage or {}
        if "retrieval_confidence" in tu:
            daily[day]["conf"].append(float(tu["retrieval_confidence"]))
        if "hallucination_risk" in tu:
            daily[day]["risk"].append(float(tu["hallucination_risk"]))
        if tu.get("response_rejected"):
            daily[day]["rejected"] += 1

    return [
        {
            "date": day,
            "avg_confidence": round(sum(v["conf"]) / len(v["conf"]), 3) if v["conf"] else 0.0,
            "avg_hallucination_risk": round(sum(v["risk"]) / len(v["risk"]), 3) if v["risk"] else 0.0,
            "rejection_count": v["rejected"],
        }
        for day, v in sorted(daily.items())
    ]


async def get_top_endpoints(
    db: AsyncSession, organization_id: UUID
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(
            MonitoringLog.endpoint,
            func.count().label("call_count"),
            func.avg(MonitoringLog.response_time_ms).label("avg_rt"),
        )
        .where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.event_type == "api_request",
            MonitoringLog.created_at >= since,
            MonitoringLog.endpoint.isnot(None),
        )
        .group_by(MonitoringLog.endpoint)
        .order_by(func.count().desc())
        .limit(10)
    )
    rows = result.all()
    return [
        {
            "endpoint": row[0],
            "call_count": int(row[1]),
            "avg_response_time_ms": round(float(row[2]), 1) if row[2] else 0.0,
        }
        for row in rows
    ]


async def get_database_performance_metrics(
    db: AsyncSession, organization_id: UUID
) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    slow_count = await db.scalar(
        select(func.count()).where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.response_time_ms > 1000,
            MonitoringLog.created_at >= since,
        )
    ) or 0
    avg_time = await db.scalar(
        select(func.avg(MonitoringLog.response_time_ms)).where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.created_at >= since,
            MonitoringLog.response_time_ms.isnot(None),
        )
    )
    return {
        "slow_query_count": int(slow_count),
        "avg_query_time_ms": round(float(avg_time), 1) if avg_time else 0.0,
    }
