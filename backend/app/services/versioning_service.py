from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.document import Document
from app.models.user import User


async def create_document_version(
    db: AsyncSession,
    parent_document_id: UUID,
    current_user: User,
    file_content: bytes,
    file_name: str,
    title: str,
    description: str | None = None,
    department_id: UUID | None = None,
    file_type: str = "",
    file_path: str = "",
) -> Document | None:
    parent_result = await db.execute(
        select(Document).where(
            Document.id == parent_document_id,
            Document.organization_id == current_user.organization_id,
        )
    )
    parent = parent_result.scalar_one_or_none()
    if parent is None:
        return None

    max_version_result = await db.execute(
        select(Document).where(
            (Document.id == parent_document_id)
            | (Document.parent_document_id == parent_document_id)
        )
    )
    existing = list(max_version_result.scalars().all())
    next_version = max((doc.version_number for doc in existing), default=1) + 1

    for doc in existing:
        if doc.status == "approved":
            doc.status = "archived"
            doc.is_approved = False

    file_size_mb = Decimal(str(round(len(file_content) / (1024 * 1024), 2)))
    new_doc = Document(
        id=uuid4(),
        organization_id=current_user.organization_id,
        department_id=department_id or parent.department_id,
        uploaded_by=current_user.id,
        title=title,
        description=description,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        file_size_mb=file_size_mb,
        status="uploaded",
        is_approved=False,
        version_number=next_version,
        parent_document_id=parent_document_id,
        malware_scan_status="pending",
        embedding_status="pending",
    )
    db.add(new_doc)

    db.add(
        AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="DOCUMENT_VERSION_CREATED",
            resource_type="document",
            resource_id=str(new_doc.id),
            new_value={
                "version_number": next_version,
                "parent_document_id": str(parent_document_id),
                "title": title,
            },
        )
    )
    await db.flush()
    return new_doc


async def get_document_versions(
    db: AsyncSession,
    document_id: UUID,
    organization_id: UUID,
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(
            Document.organization_id == organization_id,
            (Document.id == document_id) | (Document.parent_document_id == document_id),
        )
        .order_by(Document.version_number.asc())
    )
    return list(result.scalars().all())


async def get_current_version(
    db: AsyncSession,
    document_id: UUID,
    organization_id: UUID,
) -> Document | None:
    result = await db.execute(
        select(Document)
        .where(
            Document.organization_id == organization_id,
            (Document.id == document_id) | (Document.parent_document_id == document_id),
            Document.status == "approved",
            Document.is_approved.is_(True),
        )
        .order_by(Document.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def rollback_to_version(
    db: AsyncSession,
    document_id: UUID,
    version_id: UUID,
    current_user: User,
) -> Document | None:
    versions = await get_document_versions(db, document_id, current_user.organization_id)
    target = next((doc for doc in versions if doc.id == version_id), None)
    if target is None:
        return None

    for doc in versions:
        if doc.status == "approved":
            doc.status = "archived"
            doc.is_approved = False

    target.status = "approved"
    target.is_approved = True
    target.approved_by = current_user.id
    target.approved_at = datetime.now(timezone.utc)

    db.add(
        AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="DOCUMENT_VERSION_ROLLBACK",
            resource_type="document",
            resource_id=str(target.id),
            new_value={
                "rolled_back_to_version": target.version_number,
                "document_id": str(document_id),
            },
        )
    )
    await db.flush()
    return target
