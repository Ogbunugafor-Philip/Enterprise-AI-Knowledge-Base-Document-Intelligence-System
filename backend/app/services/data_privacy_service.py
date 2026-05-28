import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.chat import ChatSession, Message
from app.models.document import Document
from app.models.monitoring import MonitoringLog
from app.models.user import User
from app.schemas.compliance import DataRetentionSettings, UserDataExport


RETENTION_SETTINGS = DataRetentionSettings()


def mask_sensitive_field(value: str | None) -> str | None:
    if not value:
        return value
    if "@" in value:
        local, domain = value.split("@", 1)
        first = local[:1] or "*"
        return f"{first}***@{domain}"
    digits = re.sub(r"\D", "", value)
    if len(digits) >= 10:
        return f"***-***-{digits[-4:]}"
    return value


async def anonymize_user_data(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID | None,
    performed_by: UUID | None = None,
) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    anonymized = f"ANONYMIZED_USER_{user.id}"
    old_value = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }
    user.first_name = "Anonymized"
    user.last_name = "User"
    user.email = anonymized
    user.email_encrypted = None
    user.is_active = False

    from app.services.audit_service import log_action

    await log_action(
        db,
        user_id=performed_by,
        organization_id=organization_id,
        action="GDPR_ANONYMIZATION",
        resource_type="user",
        resource_id=str(user_id),
        old_value=old_value,
        new_value={"email": anonymized},
    )
    return user


async def apply_chat_retention_policy(
    db: AsyncSession,
    organization_id: UUID,
    retention_days: int = 365,
    performed_by: UUID | None = None,
) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await db.execute(
        select(ChatSession.id).where(ChatSession.organization_id == organization_id, ChatSession.created_at < cutoff)
    )
    session_ids = list(result.scalars().all())
    if session_ids:
        await db.execute(delete(Message).where(Message.session_id.in_(session_ids)))
        await db.execute(delete(ChatSession).where(ChatSession.id.in_(session_ids)))
    from app.services.audit_service import log_action

    await log_action(
        db,
        user_id=performed_by,
        organization_id=organization_id,
        action="CHAT_RETENTION_CLEANUP",
        resource_type="chat_session",
        new_value={"deleted_sessions": len(session_ids), "retention_days": retention_days},
    )
    return len(session_ids)


async def apply_document_retention_policy(
    db: AsyncSession,
    organization_id: UUID,
    retention_days: int = 2555,
    performed_by: UUID | None = None,
    delete_expired: bool = False,
) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await db.execute(
        select(Document).where(Document.organization_id == organization_id, Document.created_at < cutoff)
    )
    documents = list(result.scalars().all())
    for document in documents:
        document.status = "deleted" if delete_expired else "archived"
        document.is_approved = False
    from app.services.audit_service import log_action

    await log_action(
        db,
        user_id=performed_by,
        organization_id=organization_id,
        action="DOCUMENT_RETENTION_APPLIED",
        resource_type="document",
        new_value={"affected_documents": len(documents), "retention_days": retention_days, "delete_expired": delete_expired},
    )
    return len(documents)


async def apply_monitoring_log_retention(
    db: AsyncSession,
    organization_id: UUID,
    retention_days: int = 90,
    performed_by: UUID | None = None,
) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await db.execute(
        select(MonitoringLog.id).where(MonitoringLog.organization_id == organization_id, MonitoringLog.created_at < cutoff)
    )
    ids = list(result.scalars().all())
    if ids:
        await db.execute(delete(MonitoringLog).where(MonitoringLog.id.in_(ids)))
    from app.services.audit_service import log_action

    await log_action(
        db,
        user_id=performed_by,
        organization_id=organization_id,
        action="MONITORING_LOG_RETENTION_CLEANUP",
        resource_type="monitoring_log",
        new_value={"deleted_logs": len(ids), "retention_days": retention_days},
    )
    return len(ids)


async def apply_audit_log_retention(
    db: AsyncSession,
    organization_id: UUID,
    retention_days: int | None = None,
    performed_by: UUID | None = None,
) -> int:
    days = retention_days or RETENTION_SETTINGS.audit_log_retention_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(select(AuditLog.id).where(AuditLog.organization_id == organization_id, AuditLog.created_at < cutoff))
    ids = list(result.scalars().all())
    if ids:
        await db.execute(delete(AuditLog).where(AuditLog.id.in_(ids)))
    return len(ids)


async def get_user_data_export(db: AsyncSession, user_id: UUID) -> UserDataExport | None:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return None

    sessions_result = await db.execute(select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at))
    sessions = list(sessions_result.scalars().all())
    messages_result = await db.execute(select(Message).where(Message.user_id == user_id).order_by(Message.created_at))
    messages = list(messages_result.scalars().all())
    audit_result = await db.execute(select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at))
    audit_entries = list(audit_result.scalars().all())

    return UserDataExport(
        user_id=user.id,
        export_date=datetime.now(timezone.utc),
        profile_data={
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "organization_id": str(user.organization_id) if user.organization_id else None,
            "department_id": str(user.department_id) if user.department_id else None,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        chat_history=[
            {
                "session_id": str(session.id),
                "title": session.title,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "messages": [
                    {
                        "id": str(message.id),
                        "role": message.role,
                        "content": message.content,
                        "created_at": message.created_at.isoformat() if message.created_at else None,
                    }
                    for message in messages
                    if message.session_id == session.id
                ],
            }
            for session in sessions
        ],
        ai_queries=[
            {
                "id": str(message.id),
                "content": message.content,
                "confidence_score": float(message.confidence_score) if message.confidence_score is not None else None,
                "source_documents": message.source_documents,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            }
            for message in messages
            if message.role == "assistant"
        ],
        audit_entries=[
            {
                "id": str(entry.id),
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "status": entry.status,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in audit_entries
        ],
    )
