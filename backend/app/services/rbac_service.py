from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionEnum, RoleEnum, ROLE_PERMISSIONS, has_permission, normalize_role
from app.models.chat import ChatSession
from app.models.document import Document, DocumentAccess
from app.models.user import User


def get_user_permissions(user: User) -> list[PermissionEnum]:
    role = normalize_role(user.role.name if user.role else None)
    if role is None:
        return []
    return sorted(ROLE_PERMISSIONS[role], key=lambda permission: permission.value)


async def check_document_access(db: AsyncSession, user: User, document: Document) -> bool:
    role = normalize_role(user.role.name if user.role else None)
    if role == RoleEnum.SUPER_ADMIN:
        return True
    if document.organization_id != user.organization_id:
        return False
    if not document.is_approved or document.status in {"archived", "deleted", "expired"}:
        return False
    if document.department_id and document.department_id != user.department_id:
        access_result = await db.execute(
            select(DocumentAccess).where(
                DocumentAccess.document_id == document.id,
                DocumentAccess.organization_id == user.organization_id,
                or_(
                    DocumentAccess.user_id == user.id,
                    DocumentAccess.role_id == user.role_id,
                    DocumentAccess.department_id == user.department_id,
                ),
            )
        )
        return access_result.scalars().first() is not None
    return has_permission(role, PermissionEnum.DOCUMENT_VIEW)


def check_chat_isolation(user: User, session: ChatSession) -> bool:
    role = normalize_role(user.role.name if user.role else None)
    if role == RoleEnum.SUPER_ADMIN:
        return True
    if role == RoleEnum.ADMIN:
        return session.organization_id == user.organization_id
    return session.user_id == user.id


async def get_accessible_documents(db: AsyncSession, user: User) -> list[UUID]:
    role = normalize_role(user.role.name if user.role else None)
    query = select(Document.id).where(Document.is_approved.is_(True), Document.status == "approved")
    if role != RoleEnum.SUPER_ADMIN:
        query = query.where(Document.organization_id == user.organization_id)
    if role == RoleEnum.USER:
        query = query.outerjoin(DocumentAccess, DocumentAccess.document_id == Document.id).where(
            or_(
                Document.department_id.is_(None),
                Document.department_id == user.department_id,
                DocumentAccess.user_id == user.id,
                DocumentAccess.role_id == user.role_id,
                DocumentAccess.department_id == user.department_id,
            )
        )
    result = await db.execute(query)
    return list(result.scalars().all())


def filter_by_tenant(query, model, organization_id: UUID | None):
    if organization_id is None:
        return query
    return query.where(model.organization_id == organization_id)
