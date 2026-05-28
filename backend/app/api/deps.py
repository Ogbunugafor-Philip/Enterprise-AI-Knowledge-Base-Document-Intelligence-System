from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Annotated, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import PermissionEnum, RoleEnum, has_permission, normalize_role
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass(frozen=True)
class TenantContext:
    organization_id: UUID | None
    user_id: UUID
    role: RoleEnum | None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload["sub"]))
        organization_id = UUID(str(payload["organization_id"])) if payload.get("organization_id") else None
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    current_user = await get_current_active_user_allow_password_change(current_user)
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required. Please change your temporary password before accessing the platform.",
        )
    return current_user


async def get_current_active_user_allow_password_change(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not verified")
    return current_user


def require_role(allowed_roles: list[RoleEnum | str]) -> Callable:
    async def role_dependency(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        role = normalize_role(current_user.role.name if current_user.role else None)
        normalized_allowed = {normalize_role(role_name) for role_name in allowed_roles}
        if role not in normalized_allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if role != RoleEnum.SUPER_ADMIN and current_user.organization_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization context required")
        return current_user

    return role_dependency


def require_permission(permission: PermissionEnum) -> Callable:
    async def permission_dependency(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        role_name = current_user.role.name if current_user.role else None
        if not has_permission(role_name, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return current_user

    return permission_dependency


async def get_tenant_context(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TenantContext:
    return TenantContext(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        role=normalize_role(current_user.role.name if current_user.role else None),
    )


async def get_organization_id(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UUID | None:
    return current_user.organization_id


def verify_same_organization(
    target_organization_id: UUID | None,
    current_user: User,
) -> None:
    role = normalize_role(current_user.role.name if current_user.role else None)
    if role == RoleEnum.SUPER_ADMIN:
        return
    if current_user.organization_id is None or target_organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")


def verify_own_resource(
    resource_user_id: UUID,
    current_user_id: UUID,
    current_user_role: RoleEnum | str | None = RoleEnum.USER,
) -> None:
    role = normalize_role(current_user_role)
    if role in {RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN}:
        return
    if resource_user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource access denied")


def check_account_not_locked(user: User) -> None:
    if user.locked_until is None:
        return
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    if locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account is temporarily locked")
