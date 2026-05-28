from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.core.rate_limiter import rate_limiter
from app.models.monitoring import MonitoringLog
from app.models.user import User
from app.schemas.security import SecurityChecklistReport, SecurityEvent
from app.services import security_scan_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/security", tags=["security"])
_SUPER_ADMIN_DEP = Depends(require_role([RoleEnum.SUPER_ADMIN]))


@router.get("/checklist", response_model=SecurityChecklistReport, dependencies=[_SUPER_ADMIN_DEP])
async def security_checklist(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> SecurityChecklistReport:
    return await security_scan_service.generate_security_report()


@router.get("/rate-limit-status", dependencies=[_SUPER_ADMIN_DEP])
async def rate_limit_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    return rate_limiter.get_rate_limit_status()


@router.post("/rate-limit/reset", dependencies=[_SUPER_ADMIN_DEP])
async def reset_rate_limit(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    key: str = Query(...),
) -> dict:
    reset = rate_limiter.reset_rate_limit(key)
    await log_action(
        db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="RATE_LIMIT_RESET",
        resource_type="security",
        resource_id=key,
        new_value={"reset": reset},
    )
    await db.commit()
    return {"key": key, "reset": reset}


@router.get("/events", response_model=list[SecurityEvent], dependencies=[_SUPER_ADMIN_DEP])
async def security_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    event_type: str | None = Query(default=None, pattern="^(sql_injection|rate_limit_exceeded|role_bypass|isolation_violation)$"),
) -> list[SecurityEvent]:
    allowed = ["sql_injection", "rate_limit_exceeded", "role_bypass", "isolation_violation"]
    query = select(MonitoringLog).where(MonitoringLog.event_type.in_(allowed))
    if current_user.organization_id is not None:
        query = query.where(MonitoringLog.organization_id == current_user.organization_id)
    if event_type:
        query = query.where(MonitoringLog.event_type == event_type)
    result = await db.execute(query.order_by(MonitoringLog.created_at.desc()).limit(100))
    return [
        SecurityEvent(
            event_type=event.event_type,
            severity=(event.token_usage or {}).get("severity", "medium") if event.token_usage else "medium",
            ip_address=event.ip_address,
            endpoint=event.endpoint,
            description=event.error_message,
            created_at=event.created_at,
        )
        for event in result.scalars().all()
    ]
