from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.audit import AuditLog
from app.models.user import User
from app.services import rag_logging_service

router = APIRouter(prefix="/rag", tags=["rag-analytics"])

_ADMIN_DEP = Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))


@router.get("/analytics", dependencies=[_ADMIN_DEP])
async def get_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    return await rag_logging_service.get_ai_quality_analytics(
        db, current_user.organization_id, days=days
    )


@router.get("/low-confidence-flags", dependencies=[_ADMIN_DEP])
async def list_low_confidence_flags(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return await rag_logging_service.get_low_confidence_flags(
        db, current_user.organization_id, page=page, page_size=page_size
    )


@router.post("/low-confidence-flags/{flag_id}/review", dependencies=[_ADMIN_DEP])
async def review_flag(
    flag_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    from sqlalchemy import select
    from app.models.monitoring import SystemAlert

    result = await db.execute(
        select(SystemAlert).where(
            SystemAlert.id == flag_id,
            SystemAlert.organization_id == current_user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")

    alert.status = "resolved"
    db.add(
        AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="LOW_CONFIDENCE_FLAG_REVIEWED",
            resource_type="system_alert",
            resource_id=str(alert.id),
        )
    )
    await db.commit()
    return {"id": str(alert.id), "status": alert.status, "reviewed": True}
