from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.user import User
from app.schemas.compliance import (
    AuditLogDetailResponse,
    AuditLogListResponse,
    ComplianceReportRequest,
    DataRetentionSettings,
    UserDataExport,
)
from app.services import audit_service, compliance_service, data_privacy_service

router = APIRouter(prefix="/compliance", tags=["compliance"])

_ADMIN_DEP = Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))
_SUPER_ADMIN_DEP = Depends(require_role([RoleEnum.SUPER_ADMIN]))


@router.get("/audit-logs", response_model=AuditLogListResponse, dependencies=[_ADMIN_DEP])
async def audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditLogListResponse:
    return await audit_service.get_audit_logs(
        db,
        current_user,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/audit-logs/export", dependencies=[_SUPER_ADMIN_DEP])
async def audit_logs_export(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> Response:
    content = await audit_service.export_audit_logs(
        db,
        current_user,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


@router.get("/audit-logs/{log_id}", response_model=AuditLogDetailResponse, dependencies=[_ADMIN_DEP])
async def audit_log_detail(
    log_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> AuditLogDetailResponse:
    detail = await audit_service.get_audit_log_detail(db, current_user, log_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return detail


@router.post("/reports/generate", dependencies=[_SUPER_ADMIN_DEP])
async def generate_report(
    payload: ComplianceReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Response:
    report = await compliance_service.generate_compliance_report(
        db,
        report_type=payload.report_type,
        organization_id=current_user.organization_id,
        generated_by=current_user.id,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    if payload.format == "csv":
        content = compliance_service.export_compliance_report_csv(report)
        media_type = "text/csv"
        filename = f"{payload.report_type}_compliance_report.csv"
    else:
        content = await compliance_service.export_compliance_report_pdf(db, report)
        media_type = "application/pdf"
        filename = f"{payload.report_type}_compliance_report.pdf"
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/reports/activity", dependencies=[_ADMIN_DEP])
async def activity_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> dict:
    return await compliance_service.generate_activity_report(db, current_user.organization_id, date_from, date_to)


@router.get("/reports/security", dependencies=[_SUPER_ADMIN_DEP])
async def security_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> dict:
    return await compliance_service.generate_security_report(db, current_user.organization_id, date_from, date_to)


@router.get("/user/{user_id}/activity", dependencies=[_SUPER_ADMIN_DEP])
async def user_activity(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> dict:
    return await audit_service.get_user_activity_report(db, current_user, user_id, date_from=date_from, date_to=date_to)


@router.get("/user/{user_id}/data-export", response_model=UserDataExport, dependencies=[_SUPER_ADMIN_DEP])
async def user_data_export(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserDataExport:
    export = await data_privacy_service.get_user_data_export(db, user_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return export


@router.get("/retention-settings", response_model=DataRetentionSettings, dependencies=[_ADMIN_DEP])
async def get_retention_settings(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DataRetentionSettings:
    return data_privacy_service.RETENTION_SETTINGS


@router.put("/retention-settings", response_model=DataRetentionSettings, dependencies=[_SUPER_ADMIN_DEP])
async def update_retention_settings(
    payload: DataRetentionSettings,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DataRetentionSettings:
    data_privacy_service.RETENTION_SETTINGS = payload
    return data_privacy_service.RETENTION_SETTINGS
