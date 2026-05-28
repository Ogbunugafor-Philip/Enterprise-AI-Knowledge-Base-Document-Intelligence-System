from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, validate_password_strength
from app.models.audit import AuditLog
from app.models.auth import PasswordHistory
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.schemas.auth import SuperAdminSetupRequest, SuperAdminSetupResponse

router = APIRouter(prefix="/setup", tags=["setup"])

SUPER_ADMIN_ROLE = "SUPER_ADMIN"


async def super_admin_exists(db: AsyncSession) -> bool:
    result = await db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == SUPER_ADMIN_ROLE, Role.organization_id.is_(None))
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_or_create_super_admin_role(db: AsyncSession) -> Role:
    result = await db.execute(
        select(Role).where(Role.name == SUPER_ADMIN_ROLE, Role.organization_id.is_(None))
    )
    role = result.scalar_one_or_none()
    if role is not None:
        return role

    role = Role(
        organization_id=None,
        name=SUPER_ADMIN_ROLE,
        description="Platform-level administrator with full system permissions",
        is_system_role=True,
    )
    permission = Permission(
        organization_id=None,
        name="Full system access",
        description="Allows every platform-level action",
        resource="*",
        action="*",
    )
    db.add_all([role, permission])
    await db.flush()
    db.add(RolePermission(organization_id=None, role_id=role.id, permission_id=permission.id))
    await db.flush()
    return role


@router.post("/super-admin", response_model=SuperAdminSetupResponse, status_code=status.HTTP_201_CREATED)
async def setup_super_admin(
    payload: SuperAdminSetupRequest,
    db: AsyncSession = Depends(get_db),
) -> SuperAdminSetupResponse:
    if await super_admin_exists(db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform already initialized")

    valid, errors = validate_password_strength(payload.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)

    duplicate_result = await db.execute(
        select(User).where(User.email == payload.email, User.organization_id.is_(None)).limit(1)
    )
    if duplicate_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform already initialized")

    role = await get_or_create_super_admin_role(db)
    created_at = datetime.now(timezone.utc)
    user = User(
        organization_id=None,
        department_id=None,
        role_id=role.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_verified=True,
        is_first_login=False,
        must_change_password=False,
        failed_login_attempts=0,
        password_changed_at=created_at,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(organization_id=None, user_id=user.id, role_id=role.id, assigned_by=None))
    db.add(PasswordHistory(organization_id=None, user_id=user.id, hashed_password=user.hashed_password))
    db.add(
        AuditLog(
            organization_id=None,
            user_id=user.id,
            action="SUPER_ADMIN_CREATED",
            resource_type="setup",
            resource_id=str(user.id),
            status="success",
            new_value={"email": payload.email, "role": SUPER_ADMIN_ROLE},
        )
    )
    await db.commit()

    return SuperAdminSetupResponse(
        message="Super Admin created successfully",
        email=payload.email,
        created_at=created_at,
    )
