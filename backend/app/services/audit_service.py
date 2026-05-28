import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import RoleEnum, normalize_role
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.compliance import AuditLogDetailResponse, AuditLogListResponse, AuditLogResponse
from app.services.data_privacy_service import mask_sensitive_field


def _canonical_payload(log: AuditLog) -> str:
    payload = {
        "organization_id": str(log.organization_id) if log.organization_id else None,
        "user_id": str(log.user_id) if log.user_id else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "status": log.status,
        "created_at": log.created_at.isoformat() if getattr(log, "created_at", None) else None,
        "previous_hash": log.previous_hash,
    }
    return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


def calculate_audit_hash(log: AuditLog) -> str:
    return hashlib.sha256(_canonical_payload(log).encode("utf-8")).hexdigest()


async def log_action(
    db: AsyncSession | None = None,
    *,
    user_id: UUID | None,
    organization_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    old_value: dict | list | None = None,
    new_value: dict | list | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "success",
) -> None:
    """Best-effort audit logging. This function intentionally never raises."""
    try:
        if db is None:
            return
        previous_hash = None
        try:
            previous_result = await db.execute(
                select(AuditLog.audit_hash)
                .where(AuditLog.organization_id == organization_id)
                .order_by(AuditLog.created_at.desc())
                .limit(1)
            )
            previous_hash = previous_result.scalar_one_or_none()
        except Exception:
            previous_hash = None

        log = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            previous_hash=previous_hash,
        )
        db.add(log)
        try:
            await db.flush()
        except TypeError:
            db.flush()
        if getattr(log, "created_at", None) is None:
            log.created_at = datetime.now(timezone.utc)
        log.audit_hash = calculate_audit_hash(log)
        try:
            await db.flush()
        except TypeError:
            db.flush()
    except Exception:
        return


def _authorize_audit_access(current_user: User) -> RoleEnum:
    role = normalize_role(current_user.role.name if current_user and current_user.role else None)
    if role not in {RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit logs require admin access")
    return role


def _apply_filters(
    query,
    *,
    current_user: User,
    user_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    role = _authorize_audit_access(current_user)
    if role != RoleEnum.SUPER_ADMIN:
        query = query.where(AuditLog.organization_id == current_user.organization_id)
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    return query


async def _masked_email_for_user(db: AsyncSession, user_id: UUID | None) -> str | None:
    if user_id is None:
        return None
    try:
        result = await db.execute(select(User.email).where(User.id == user_id))
        email = result.scalar_one_or_none()
        return mask_sensitive_field(email) if email else None
    except Exception:
        return None


async def _log_response(db: AsyncSession, log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        user_email_masked=await _masked_email_for_user(db, log.user_id),
        organization_id=log.organization_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        ip_address=log.ip_address,
        status=log.status,
        created_at=log.created_at,
    )


async def get_audit_logs(
    db: AsyncSession,
    current_user: User,
    *,
    user_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AuditLogListResponse:
    query = _apply_filters(
        select(AuditLog),
        current_user=current_user,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
    )
    count_query = _apply_filters(
        select(func.count()).select_from(AuditLog),
        current_user=current_user,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
    )
    total = int((await db.execute(count_query)).scalar_one() or 0)
    result = await db.execute(query.order_by(AuditLog.created_at.desc()).limit(page_size).offset((page - 1) * page_size))
    logs = list(result.scalars().all())
    return AuditLogListResponse(
        logs=[await _log_response(db, log) for log in logs],
        total_count=total,
        page=page,
        page_size=page_size,
    )


async def get_audit_log_detail(db: AsyncSession, current_user: User, log_id: UUID) -> AuditLogDetailResponse | None:
    _authorize_audit_access(current_user)
    query = select(AuditLog).where(AuditLog.id == log_id)
    if normalize_role(current_user.role.name if current_user.role else None) != RoleEnum.SUPER_ADMIN:
        query = query.where(AuditLog.organization_id == current_user.organization_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    if log is None:
        return None
    base = await _log_response(db, log)
    return AuditLogDetailResponse(
        **base.model_dump(),
        old_value=log.old_value,
        new_value=log.new_value,
        user_agent=log.user_agent,
        previous_hash=log.previous_hash,
        audit_hash=log.audit_hash,
    )


async def export_audit_logs(db: AsyncSession, current_user: User, **filters: Any) -> bytes:
    response = await get_audit_logs(db, current_user, page=1, page_size=100, **filters)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["created_at", "organization_id", "user_id", "action", "resource_type", "resource_id", "status", "ip_address"])
    for log in response.logs:
        writer.writerow([
            log.created_at.isoformat(),
            log.organization_id,
            log.user_id,
            log.action,
            log.resource_type,
            log.resource_id,
            log.status,
            log.ip_address,
        ])
    return output.getvalue().encode("utf-8")


async def verify_audit_log_integrity(db: AsyncSession, organization_id: UUID | None = None) -> dict:
    query = select(AuditLog)
    if organization_id is not None:
        query = query.where(AuditLog.organization_id == organization_id)
    result = await db.execute(query.order_by(AuditLog.created_at.asc()))
    logs = list(result.scalars().all())
    violations = []
    previous_hash = None
    for log in logs:
        if log.previous_hash != previous_hash:
            violations.append({"id": str(log.id), "reason": "previous_hash_mismatch"})
        expected_hash = calculate_audit_hash(log)
        if log.audit_hash and log.audit_hash != expected_hash:
            violations.append({"id": str(log.id), "reason": "audit_hash_mismatch"})
        previous_hash = log.audit_hash
    return {"checked": len(logs), "valid": len(violations) == 0, "violations": violations}


async def get_user_activity_report(
    db: AsyncSession,
    current_user: User,
    target_user_id: UUID,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    role = _authorize_audit_access(current_user)
    query = select(AuditLog).where(AuditLog.user_id == target_user_id)
    if role != RoleEnum.SUPER_ADMIN:
        query = query.where(AuditLog.organization_id == current_user.organization_id)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    result = await db.execute(query.order_by(AuditLog.created_at.desc()))
    logs = list(result.scalars().all())
    return {
        "user_id": str(target_user_id),
        "total_actions": len(logs),
        "actions": [
            {
                "id": str(log.id),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "status": log.status,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "login_history": [
            {"action": log.action, "created_at": log.created_at.isoformat() if log.created_at else None, "status": log.status}
            for log in logs
            if "LOGIN" in log.action
        ],
    }
