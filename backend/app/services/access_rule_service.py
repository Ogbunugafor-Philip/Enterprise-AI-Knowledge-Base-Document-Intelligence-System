from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.document import Document, DocumentAccess
from app.models.user import User


async def create_access_rule(
    db: AsyncSession,
    document_id: UUID,
    current_user: User,
    access_type: str,
    department_id: UUID | None = None,
    role_id: UUID | None = None,
    user_id: UUID | None = None,
) -> DocumentAccess | None:
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id,
        )
    )
    if doc_result.scalar_one_or_none() is None:
        return None

    rule = DocumentAccess(
        document_id=document_id,
        organization_id=current_user.organization_id,
        access_type=access_type,
        department_id=department_id,
        role_id=role_id,
        user_id=user_id,
        granted_by=current_user.id,
    )
    db.add(rule)
    from app.services.audit_service import log_action

    await log_action(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="DOCUMENT_ACCESS_RULE_CREATED",
        resource_type="document_access",
        resource_id=str(document_id),
        new_value={
            "access_type": access_type,
            "department_id": str(department_id) if department_id else None,
            "role_id": str(role_id) if role_id else None,
            "user_id": str(user_id) if user_id else None,
        },
    )
    await db.flush()
    return rule


async def get_document_access_rules(
    db: AsyncSession,
    document_id: UUID,
    organization_id: UUID,
) -> list[DocumentAccess]:
    result = await db.execute(
        select(DocumentAccess).where(
            DocumentAccess.document_id == document_id,
            DocumentAccess.organization_id == organization_id,
        )
    )
    return list(result.scalars().all())


async def delete_access_rule(
    db: AsyncSession,
    rule_id: UUID,
    organization_id: UUID,
    current_user: User,
) -> bool:
    result = await db.execute(
        select(DocumentAccess).where(
            DocumentAccess.id == rule_id,
            DocumentAccess.organization_id == organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        return False

    from app.services.audit_service import log_action

    await log_action(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="DOCUMENT_ACCESS_RULE_DELETED",
        resource_type="document_access",
        resource_id=str(rule.document_id),
        old_value={
            "rule_id": str(rule.id),
            "access_type": rule.access_type,
        },
    )
    await db.delete(rule)
    await db.flush()
    return True


async def check_user_document_access(
    db: AsyncSession,
    user: User,
    document: Document,
) -> bool:
    from app.core.permissions import RoleEnum, normalize_role

    role = normalize_role(user.role.name if user.role else None)
    if role == RoleEnum.SUPER_ADMIN:
        return True
    if document.organization_id != user.organization_id:
        return False
    if document.status != "approved" or not document.is_approved:
        return False

    # Organization-wide: no department restriction
    if document.department_id is None:
        return True

    # Department match
    if document.department_id == user.department_id:
        return True

    # DocumentAccess table rules
    access_result = await db.execute(
        select(DocumentAccess).where(
            DocumentAccess.document_id == document.id,
            DocumentAccess.organization_id == user.organization_id,
            or_(
                DocumentAccess.user_id == user.id,
                DocumentAccess.role_id == user.role_id,
                DocumentAccess.department_id == user.department_id,
                DocumentAccess.access_type == "organization",
            ),
        )
    )
    return access_result.scalars().first() is not None


async def get_user_accessible_document_ids(
    db: AsyncSession,
    user: User,
) -> list[UUID]:
    from app.core.permissions import RoleEnum, normalize_role

    role = normalize_role(user.role.name if user.role else None)
    base_query = select(Document.id).where(
        Document.is_approved.is_(True),
        Document.status == "approved",
    )
    if role != RoleEnum.SUPER_ADMIN:
        base_query = base_query.where(Document.organization_id == user.organization_id)

    if role == RoleEnum.USER:
        base_query = base_query.outerjoin(
            DocumentAccess, DocumentAccess.document_id == Document.id
        ).where(
            or_(
                Document.department_id.is_(None),
                Document.department_id == user.department_id,
                DocumentAccess.user_id == user.id,
                DocumentAccess.role_id == user.role_id,
                DocumentAccess.department_id == user.department_id,
                DocumentAccess.access_type == "organization",
            )
        )

    result = await db.execute(base_query)
    return list(result.scalars().all())
