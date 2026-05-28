from datetime import datetime, timedelta, timezone
import os
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.encryption import encrypt_field, hash_sensitive_data
from app.core.security import generate_otp_code, generate_temporary_password, hash_password
from app.models.audit import AuditLog
from app.models.auth import OTPVerification, PasswordHistory
from app.models.department import Department
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.schemas.user_management import (
    BulkUserError,
    PasswordResetByAdminResponse,
    SuperAdminDashboardStats,
    UserActivationResponse,
    UserCreateResponse,
    UserDetailResponse,
    UserListResponse,
)

OTP_EXPIRY_MINUTES = 10


def _running_under_pytest() -> bool:
    return bool(os.getenv("PYTEST_CURRENT_TEST"))


def _user_detail(user: User) -> UserDetailResponse:
    return UserDetailResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        organization_id=user.organization_id,
        role=user.role.name if user.role else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_first_login=user.is_first_login,
        must_change_password=user.must_change_password,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        last_login=user.last_login,
        password_changed_at=user.password_changed_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _user_create_response(user: User, temp_password: str | None = None) -> UserCreateResponse:
    return UserCreateResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        department_id=user.department_id,
        organization_id=user.organization_id,
        role=user.role.name if user.role else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


async def create_user(
    db: AsyncSession,
    first_name: str,
    last_name: str,
    email: str,
    organization_id: UUID,
    role_id: UUID | None,
    department_id: UUID | None,
    send_welcome_email: bool,
    created_by_user_id: UUID | None = None,
) -> User:
    existing = await db.execute(
        select(User).where(User.organization_id == organization_id, User.email == email)
    )
    if existing.scalar_one_or_none() is not None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered in this organization")

    if department_id is not None:
        dept = await db.execute(
            select(Department).where(Department.id == department_id, Department.organization_id == organization_id)
        )
        if dept.scalar_one_or_none() is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found in this organization")

    if role_id is not None:
        role_check = await db.execute(select(Role).where(Role.id == role_id))
        if role_check.scalar_one_or_none() is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")

    temp_password = generate_temporary_password()
    hashed = hash_password(temp_password)

    user = User(
        organization_id=organization_id,
        department_id=department_id,
        role_id=role_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        email_encrypted=encrypt_field(email),
        hashed_password=hashed,
        is_active=True,
        is_verified=False,
        is_first_login=True,
        must_change_password=True,
        failed_login_attempts=0,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    db.add(PasswordHistory(organization_id=organization_id, user_id=user.id, hashed_password=hashed))

    otp_code = generate_otp_code()
    db.add(
        OTPVerification(
            organization_id=organization_id,
            user_id=user.id,
            otp_code=hash_sensitive_data(otp_code),
            otp_code_hash=hash_sensitive_data(otp_code),
            otp_type="verification",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )
    )
    from app.services.audit_service import log_action

    await log_action(
        db,
        organization_id=organization_id,
        user_id=created_by_user_id,
        action="USER_CREATED",
        resource_type="user",
        resource_id=str(user.id),
        new_value={"email": email, "role_id": str(role_id) if role_id else None},
    )
    if role_id:
        await log_action(
            db,
            organization_id=organization_id,
            user_id=created_by_user_id,
            action="ROLE_ASSIGNED",
            resource_type="user",
            resource_id=str(user.id),
            new_value={"role_id": str(role_id)},
        )
    await db.flush()

    if send_welcome_email and not _running_under_pytest():
        try:
            from app.core.email import send_otp_verification_email, send_temporary_password_email
            import asyncio
            asyncio.ensure_future(send_otp_verification_email(email, otp_code))
            asyncio.ensure_future(send_temporary_password_email(email, temp_password))
        except Exception:
            pass

    refreshed = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.department)).where(User.id == user.id)
    )
    return refreshed.scalar_one()


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    first_name: str | None,
    last_name: str | None,
    department_id: UUID | None,
    role_id: UUID | None,
    is_active: bool | None,
    updated_by_user_id: UUID | None = None,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    old_values = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "department_id": str(user.department_id) if user.department_id else None,
        "role_id": str(user.role_id) if user.role_id else None,
        "is_active": user.is_active,
    }

    if department_id is not None:
        dept = await db.execute(
            select(Department).where(Department.id == department_id, Department.organization_id == organization_id)
        )
        if dept.scalar_one_or_none() is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found in this organization")
        user.department_id = department_id

    if role_id is not None:
        role_check = await db.execute(select(Role).where(Role.id == role_id))
        if role_check.scalar_one_or_none() is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")
        user.role_id = role_id

    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if is_active is not None:
        user.is_active = is_active

    from app.services.audit_service import log_action

    await log_action(
        db,
        organization_id=organization_id,
        user_id=updated_by_user_id,
        action="USER_UPDATED",
        resource_type="user",
        resource_id=str(user.id),
        old_value=old_values,
        new_value={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "department_id": str(user.department_id) if user.department_id else None,
            "role_id": str(user.role_id) if user.role_id else None,
            "is_active": user.is_active,
        },
    )
    if role_id is not None and str(role_id) != old_values["role_id"]:
        await log_action(db, organization_id=organization_id, user_id=updated_by_user_id, action="ROLE_ASSIGNED", resource_type="user", resource_id=str(user.id), old_value={"role_id": old_values["role_id"]}, new_value={"role_id": str(role_id)})
    if department_id is not None and str(department_id) != old_values["department_id"]:
        await log_action(db, organization_id=organization_id, user_id=updated_by_user_id, action="DEPARTMENT_CHANGED", resource_type="user", resource_id=str(user.id), old_value={"department_id": old_values["department_id"]}, new_value={"department_id": str(department_id)})
    await db.flush()
    refreshed = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.department)).where(User.id == user.id)
    )
    return refreshed.scalar_one()


async def activate_user(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    activated_by_user_id: UUID | None = None,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None

    from app.services.audit_service import log_action
    await log_action(db, organization_id=organization_id, user_id=activated_by_user_id, action="USER_ACTIVATED", resource_type="user", resource_id=str(user.id))
    await db.flush()
    return user


async def deactivate_user(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    reason: str | None,
    deactivated_by_user_id: UUID | None = None,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    user.is_active = False

    from app.services.audit_service import log_action
    await log_action(db, organization_id=organization_id, user_id=deactivated_by_user_id, action="USER_DEACTIVATED", resource_type="user", resource_id=str(user.id), new_value={"reason": reason})
    await db.flush()
    return user


async def delete_user(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    deleted_by_user_id: UUID | None = None,
) -> bool:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return False

    from app.services.audit_service import log_action
    from app.services.data_privacy_service import anonymize_user_data

    await anonymize_user_data(db, user.id, organization_id, deleted_by_user_id)
    await log_action(db, organization_id=organization_id, user_id=deleted_by_user_id, action="USER_DELETED", resource_type="user", resource_id=str(user.id))
    await db.flush()
    return True


async def reset_user_password_by_admin(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    force_change_on_login: bool,
    reset_by_user_id: UUID | None = None,
) -> PasswordResetByAdminResponse | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    db.add(PasswordHistory(organization_id=organization_id, user_id=user.id, hashed_password=user.hashed_password))

    temp_password = generate_temporary_password()
    user.hashed_password = hash_password(temp_password)
    user.password_changed_at = datetime.now(timezone.utc)
    if force_change_on_login:
        user.must_change_password = True

    db.add(PasswordHistory(organization_id=organization_id, user_id=user.id, hashed_password=user.hashed_password))
    from app.services.audit_service import log_action
    await log_action(db, organization_id=organization_id, user_id=reset_by_user_id, action="ADMIN_PASSWORD_RESET", resource_type="user", resource_id=str(user.id))
    await db.flush()

    email_sent = False
    try:
        if _running_under_pytest():
            raise RuntimeError("Email disabled under pytest")
        from app.core.email import send_temporary_password_email
        import asyncio
        asyncio.ensure_future(send_temporary_password_email(user.email, temp_password))
        email_sent = True
    except Exception:
        pass

    return PasswordResetByAdminResponse(
        user_id=user.id,
        email=user.email,
        temporary_password_sent=email_sent,
        force_change_on_login=force_change_on_login,
    )


async def unlock_user_account(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    unlocked_by_user_id: UUID | None = None,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    user.locked_until = None
    user.failed_login_attempts = 0

    from app.services.audit_service import log_action
    await log_action(db, organization_id=organization_id, user_id=unlocked_by_user_id, action="ACCOUNT_UNLOCKED", resource_type="user", resource_id=str(user.id))
    await db.flush()
    return user


async def get_user_list(
    db: AsyncSession,
    organization_id: UUID | None,
    department_id: UUID | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    is_verified: bool | None = None,
    search_query: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> UserListResponse:
    filters = []
    if organization_id is not None:
        filters.append(User.organization_id == organization_id)
    if department_id is not None:
        filters.append(User.department_id == department_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    else:
        filters.append(User.is_active.is_(True))
    if is_verified is not None:
        filters.append(User.is_verified == is_verified)
    if search_query:
        term = f"%{search_query}%"
        filters.append(
            or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
            )
        )

    base_query = select(User)
    if filters:
        base_query = base_query.where(and_(*filters))

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = int(count_result.scalar_one())

    offset = (page - 1) * page_size
    users_result = await db.execute(
        base_query.options(selectinload(User.role), selectinload(User.department)).order_by(User.created_at.desc()).limit(page_size).offset(offset)
    )
    users = list(users_result.scalars().all())

    return UserListResponse(
        users=[_user_detail(u) for u in users],
        total_count=total,
        page=page,
        page_size=page_size,
    )


async def get_user_detail(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID | None,
) -> UserDetailResponse | None:
    query = select(User).options(selectinload(User.role), selectinload(User.department)).where(User.id == user_id)
    if organization_id is not None:
        query = query.where(User.organization_id == organization_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user is None:
        return None
    return _user_detail(user)


async def get_superadmin_dashboard_stats(
    db: AsyncSession,
    organization_id: UUID | None = None,
) -> SuperAdminDashboardStats:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    user_base = select(func.count()).select_from(User)
    if organization_id:
        user_base = user_base.where(User.organization_id == organization_id)

    total_orgs_result = await db.execute(
        select(func.count()).select_from(Organization).where(Organization.is_active.is_(True))
        if organization_id is None
        else select(func.count()).select_from(Organization).where(Organization.id == organization_id)
    )
    total_users = await db.scalar(user_base) or 0

    active_q = select(func.count()).select_from(User).where(User.is_active.is_(True))
    inactive_q = select(func.count()).select_from(User).where(User.is_active.is_(False))
    unverified_q = select(func.count()).select_from(User).where(User.is_verified.is_(False))
    locked_q = select(func.count()).select_from(User).where(
        User.locked_until.isnot(None), User.locked_until > now
    )
    today_q = select(func.count()).select_from(User).where(User.created_at >= today_start)
    month_q = select(func.count()).select_from(User).where(User.created_at >= month_start)
    dept_q = select(func.count()).select_from(Department)

    if organization_id:
        active_q = active_q.where(User.organization_id == organization_id)
        inactive_q = inactive_q.where(User.organization_id == organization_id)
        unverified_q = unverified_q.where(User.organization_id == organization_id)
        locked_q = locked_q.where(User.organization_id == organization_id)
        today_q = today_q.where(User.organization_id == organization_id)
        month_q = month_q.where(User.organization_id == organization_id)
        dept_q = dept_q.where(Department.organization_id == organization_id)

    active_users = await db.scalar(active_q) or 0
    inactive_users = await db.scalar(inactive_q) or 0
    unverified = await db.scalar(unverified_q) or 0
    locked = await db.scalar(locked_q) or 0
    today_count = await db.scalar(today_q) or 0
    month_count = await db.scalar(month_q) or 0
    dept_count = await db.scalar(dept_q) or 0

    audit_q = (
        select(AuditLog)
        .where(AuditLog.action.in_(["USER_CREATED", "USER_ACTIVATED", "USER_DEACTIVATED", "ADMIN_PASSWORD_RESET", "USER_DELETED"]))
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    if organization_id:
        audit_q = audit_q.where(AuditLog.organization_id == organization_id)
    audit_result = await db.execute(audit_q)
    recent_logs = list(audit_result.scalars().all())

    return SuperAdminDashboardStats(
        total_organizations=int(total_orgs_result.scalar_one() or 0),
        total_users=int(total_users),
        active_users=int(active_users),
        inactive_users=int(inactive_users),
        unverified_users=int(unverified),
        locked_accounts=int(locked),
        users_created_today=int(today_count),
        users_created_this_month=int(month_count),
        departments_count=int(dept_count),
        recent_user_activity=[
            {
                "id": str(log.id),
                "action": log.action,
                "resource_id": log.resource_id,
                "user_id": str(log.user_id) if log.user_id else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in recent_logs
        ],
    )
