from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionEnum, RoleEnum, ROLE_PERMISSIONS, has_permission, normalize_role
from app.models.chat import ChatSession
from app.models.document import Document
from app.models.user import User


def get_user_permissions(user: User) -> list[PermissionEnum]:
    role = normalize_role(user.role.name if user.role else None)
    if role is None:
        return []
    return sorted(ROLE_PERMISSIONS[role], key=lambda permission: permission.value)


async def check_document_access(db: AsyncSession, user: User, document: Document) -> bool:
    from app.services.access_rule_service import check_user_document_access

    allowed = await check_user_document_access(db, user, document)
    if not allowed:
        from app.services.audit_service import log_action
        await log_action(db, organization_id=user.organization_id, user_id=user.id, action="PERMISSION_DENIED", resource_type="document", resource_id=str(document.id), status="blocked")
    return allowed


def check_chat_isolation(user: User, session: ChatSession) -> bool:
    role = normalize_role(user.role.name if user.role else None)
    if role == RoleEnum.SUPER_ADMIN:
        return True
    if role == RoleEnum.ADMIN:
        return session.organization_id == user.organization_id
    return session.user_id == user.id


async def get_accessible_documents(db: AsyncSession, user: User) -> list[UUID]:
    from app.services.access_rule_service import get_user_accessible_document_ids

    return await get_user_accessible_document_ids(db, user)


def filter_by_tenant(query, model, organization_id: UUID | None):
    if organization_id is None:
        return query
    return query.where(model.organization_id == organization_id)


async def log_role_bypass_attempt(db: AsyncSession, user: User, resource_type: str, resource_id: str | None = None) -> None:
    from app.services.audit_service import log_action
    await log_action(db, organization_id=user.organization_id, user_id=user.id, action="ROLE_BYPASS_ATTEMPTED", resource_type=resource_type, resource_id=resource_id, status="blocked")


async def log_isolation_violation(db: AsyncSession, user: User, resource_type: str, resource_id: str | None = None) -> None:
    from app.services.audit_service import log_action
    await log_action(db, organization_id=user.organization_id, user_id=user.id, action="ISOLATION_VIOLATION", resource_type=resource_type, resource_id=resource_id, status="blocked")
