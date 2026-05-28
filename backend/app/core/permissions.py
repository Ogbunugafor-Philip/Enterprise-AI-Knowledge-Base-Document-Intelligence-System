from enum import StrEnum
from functools import wraps

from fastapi import HTTPException, status


class RoleEnum(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class PermissionEnum(StrEnum):
    CHAT_ASK_QUESTION = "CHAT_ASK_QUESTION"
    CHAT_VIEW_OWN_HISTORY = "CHAT_VIEW_OWN_HISTORY"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_VIEW = "DOCUMENT_VIEW"
    DOCUMENT_APPROVE = "DOCUMENT_APPROVE"
    DOCUMENT_REJECT = "DOCUMENT_REJECT"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    DOCUMENT_MANAGE = "DOCUMENT_MANAGE"
    USER_CREATE = "USER_CREATE"
    USER_VIEW = "USER_VIEW"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_MANAGE = "USER_MANAGE"
    ROLE_CREATE = "ROLE_CREATE"
    ROLE_UPDATE = "ROLE_UPDATE"
    ROLE_DELETE = "ROLE_DELETE"
    ROLE_MANAGE = "ROLE_MANAGE"
    DEPARTMENT_VIEW = "DEPARTMENT_VIEW"
    DEPARTMENT_CREATE = "DEPARTMENT_CREATE"
    DEPARTMENT_UPDATE = "DEPARTMENT_UPDATE"
    DEPARTMENT_DELETE = "DEPARTMENT_DELETE"
    DEPARTMENT_MANAGE = "DEPARTMENT_MANAGE"
    ORGANIZATION_VIEW = "ORGANIZATION_VIEW"
    ORGANIZATION_MANAGE = "ORGANIZATION_MANAGE"
    MONITORING_VIEW = "MONITORING_VIEW"
    MONITORING_MANAGE = "MONITORING_MANAGE"
    AUDIT_LOG_VIEW = "AUDIT_LOG_VIEW"
    SYSTEM_GOVERNANCE = "SYSTEM_GOVERNANCE"
    SUPER_ADMIN_ONLY = "SUPER_ADMIN_ONLY"


ROLE_PERMISSIONS: dict[RoleEnum, set[PermissionEnum]] = {
    RoleEnum.USER: {
        PermissionEnum.CHAT_ASK_QUESTION,
        PermissionEnum.CHAT_VIEW_OWN_HISTORY,
        PermissionEnum.DOCUMENT_VIEW,
    },
    RoleEnum.ADMIN: {
        PermissionEnum.CHAT_ASK_QUESTION,
        PermissionEnum.CHAT_VIEW_OWN_HISTORY,
        PermissionEnum.DOCUMENT_UPLOAD,
        PermissionEnum.DOCUMENT_VIEW,
        PermissionEnum.DOCUMENT_APPROVE,
        PermissionEnum.DOCUMENT_REJECT,
        PermissionEnum.DOCUMENT_DELETE,
        PermissionEnum.DOCUMENT_MANAGE,
        PermissionEnum.USER_VIEW,
        PermissionEnum.DEPARTMENT_VIEW,
        PermissionEnum.MONITORING_VIEW,
        PermissionEnum.AUDIT_LOG_VIEW,
    },
    RoleEnum.SUPER_ADMIN: set(PermissionEnum),
}


def normalize_role(role: str | RoleEnum | None) -> RoleEnum | None:
    if role is None:
        return None
    try:
        return RoleEnum(str(role).upper())
    except ValueError:
        return None


def has_permission(role: str | RoleEnum | None, permission: PermissionEnum) -> bool:
    role_enum = normalize_role(role)
    if role_enum is None:
        return False
    return permission in ROLE_PERMISSIONS[role_enum]


def require_permission(permission: PermissionEnum):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            role_name = current_user.role.name if current_user and current_user.role else None
            if not has_permission(role_name, permission):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
            return await func(*args, **kwargs)

        return wrapper

    return decorator
