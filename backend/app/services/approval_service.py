from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.document import Document
from app.models.user import User
from app.schemas.approval import KnowledgeGovernanceStats


async def get_approval_queue(
    db: AsyncSession,
    organization_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    offset = (page - 1) * page_size
    base = select(Document).where(
        Document.organization_id == organization_id,
        Document.status.in_(["uploaded", "reviewed"]),
    )
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total_pending_result = await db.execute(
        select(func.count()).where(
            Document.organization_id == organization_id,
            Document.status == "uploaded",
        )
    )
    total_reviewed_result = await db.execute(
        select(func.count()).where(
            Document.organization_id == organization_id,
            Document.status == "reviewed",
        )
    )
    docs_result = await db.execute(
        base.order_by(Document.created_at.asc()).limit(page_size).offset(offset)
    )
    documents = list(docs_result.scalars().all())
    return {
        "documents": [_doc_to_dict(doc) for doc in documents],
        "total_pending": int(total_pending_result.scalar_one()),
        "total_reviewed": int(total_reviewed_result.scalar_one()),
        "page": page,
        "page_size": page_size,
    }


async def approve_document(
    db: AsyncSession,
    document_id: UUID,
    current_user: User,
    access_level: str = "organization",
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        return None

    document.status = "approved"
    document.is_approved = True
    document.approved_by = current_user.id
    document.approved_at = datetime.now(timezone.utc)
    document.rejection_reason = None

    db.add(
        AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="DOCUMENT_APPROVED",
            resource_type="document",
            resource_id=str(document.id),
            new_value={
                "status": "approved",
                "approved_by": str(current_user.id),
                "access_level": access_level,
            },
        )
    )
    await db.flush()
    return document


async def reject_document(
    db: AsyncSession,
    document_id: UUID,
    current_user: User,
    rejection_reason: str,
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        return None

    document.status = "rejected"
    document.is_approved = False
    document.rejection_reason = rejection_reason
    document.approved_by = None
    document.approved_at = None

    db.add(
        AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="DOCUMENT_REJECTED",
            resource_type="document",
            resource_id=str(document.id),
            new_value={"status": "rejected", "rejection_reason": rejection_reason},
        )
    )

    try:
        from worker.tasks.document_tasks import delete_document_embeddings_task

        delete_document_embeddings_task.delay(
            str(document.id), str(current_user.organization_id)
        )
    except Exception:
        pass

    await db.flush()
    return document


async def get_document_approval_history(
    db: AsyncSession,
    document_id: UUID,
    organization_id: UUID,
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.organization_id == organization_id,
            AuditLog.resource_type == "document",
            AuditLog.resource_id == str(document_id),
            AuditLog.action.in_(["DOCUMENT_APPROVED", "DOCUMENT_REJECTED", "DOCUMENT_VERSION_CREATED"]),
        )
        .order_by(AuditLog.created_at.desc())
    )
    return list(result.scalars().all())


async def get_governance_stats(
    db: AsyncSession,
    organization_id: UUID,
) -> KnowledgeGovernanceStats:
    approved_count = await db.scalar(
        select(func.count()).where(
            Document.organization_id == organization_id,
            Document.status == "approved",
        )
    ) or 0
    rejected_count = await db.scalar(
        select(func.count()).where(
            Document.organization_id == organization_id,
            Document.status == "rejected",
        )
    ) or 0
    pending_count = await db.scalar(
        select(func.count()).where(
            Document.organization_id == organization_id,
            Document.status.in_(["uploaded", "reviewed"]),
        )
    ) or 0

    total_decided = approved_count + rejected_count
    approval_rate = round((approved_count / total_decided * 100), 1) if total_decided > 0 else 0.0

    avg_hours_result = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    Document.approved_at - Document.created_at,
                )
            )
        ).where(
            Document.organization_id == organization_id,
            Document.status == "approved",
            Document.approved_at.isnot(None),
        )
    )
    avg_seconds = avg_hours_result.scalar_one_or_none()
    avg_hours = round(float(avg_seconds) / 3600, 1) if avg_seconds else 0.0

    reviewer_result = await db.execute(
        select(AuditLog.user_id, func.count().label("cnt"))
        .where(
            AuditLog.organization_id == organization_id,
            AuditLog.action.in_(["DOCUMENT_APPROVED", "DOCUMENT_REJECTED"]),
            AuditLog.user_id.isnot(None),
        )
        .group_by(AuditLog.user_id)
        .order_by(func.count().desc())
        .limit(1)
    )
    top_reviewer_row = reviewer_result.first()
    most_active_reviewer = str(top_reviewer_row[0]) if top_reviewer_row else None

    return KnowledgeGovernanceStats(
        total_approved=int(approved_count),
        total_rejected=int(rejected_count),
        total_pending_review=int(pending_count),
        approval_rate_percent=approval_rate,
        avg_approval_time_hours=avg_hours,
        most_active_reviewer=most_active_reviewer,
    )


def enforce_approval_gate(document: Document) -> bool:
    if document.status != "approved" or not document.is_approved:
        return False
    if document.expires_at is not None:
        expires_at = document.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) >= expires_at:
            return False
    return True


def _doc_to_dict(document: Document) -> dict:
    return {
        "id": str(document.id),
        "title": document.title,
        "file_name": document.file_name,
        "file_type": document.file_type,
        "file_size_mb": float(document.file_size_mb),
        "status": document.status,
        "is_approved": document.is_approved,
        "department_id": str(document.department_id) if document.department_id else None,
        "uploaded_by": str(document.uploaded_by),
        "rejection_reason": document.rejection_reason,
        "version_number": document.version_number,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }
