import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    check_password_history as security_check_password_history,
    create_access_token,
    generate_otp_code,
    hash_password,
    is_otp_expired,
    validate_password_strength,
    verify_password,
)
from app.core.email import send_otp_verification_email
from app.models.audit import AuditLog
from app.models.auth import OTPVerification, PasswordHistory
from app.models.organization import Organization
from app.models.user import User

LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 30
OTP_EXPIRY_MINUTES = 10
PASSWORD_EXPIRY_DAYS = 30


async def log_audit_event(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    status_value: str = "success",
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.add(
        AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status_value,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )


async def handle_failed_login(db: AsyncSession, user: User) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
    await log_audit_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="login_failed",
        resource_type="auth",
        status_value="failed",
    )


async def reset_failed_login_attempts(db: AsyncSession, user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)


def check_account_lock(user: User) -> None:
    if user.locked_until is None:
        return
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    if locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account is temporarily locked")


async def authenticate_user(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
    result = await db.execute(select(User).where(User.email == email).order_by(User.created_at))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    check_account_lock(user)

    if user.organization_id is not None:
        org_result = await db.execute(
            select(Organization).where(Organization.id == user.organization_id, Organization.is_active.is_(True))
        )
        if org_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization is inactive")

    if not verify_password(password, user.hashed_password):
        await handle_failed_login(db, user)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_verified:
        otp = await create_otp_for_user(db, user, otp_type="verification")
        await send_otp_verification_email(user.email, otp.otp_code)
        await log_audit_event(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            action="LOGIN_BLOCKED_UNVERIFIED",
            resource_type="auth",
            status_value="failed",
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please check your email and verify your OTP before logging in.",
        )

    await reset_failed_login_attempts(db, user)
    await enforce_30_day_password_expiry(user)
    token = create_access_token(
        {
            "sub": str(user.id),
            "organization_id": str(user.organization_id) if user.organization_id else None,
            "email": user.email,
            "role": user.role.name if user.role else None,
        }
    )
    await log_audit_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="login_success",
        resource_type="auth",
    )
    await db.commit()
    await db.refresh(user)
    return user, token


async def create_otp_for_user(db: AsyncSession, user: User, otp_type: str = "verification") -> OTPVerification:
    await db.execute(
        update(OTPVerification)
        .where(
            OTPVerification.user_id == user.id,
            OTPVerification.organization_id == user.organization_id,
            OTPVerification.otp_type == otp_type,
            OTPVerification.is_used.is_(False),
        )
        .values(is_used=True)
    )
    otp = OTPVerification(
        organization_id=user.organization_id,
        user_id=user.id,
        otp_code=generate_otp_code(),
        otp_type=otp_type,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    db.add(otp)
    await db.flush()
    return otp


async def verify_user_otp(db: AsyncSession, email: str, otp_code: str) -> User:
    result = await db.execute(select(User).where(User.email == email).order_by(User.created_at))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    otp_result = await db.execute(
        select(OTPVerification)
        .where(
            OTPVerification.user_id == user.id,
            OTPVerification.organization_id == user.organization_id,
            OTPVerification.otp_code == otp_code,
            OTPVerification.otp_type == "verification",
            OTPVerification.is_used.is_(False),
        )
        .order_by(desc(OTPVerification.created_at))
    )
    otp = otp_result.scalars().first()
    if otp is None or is_otp_expired(otp.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")

    otp.is_used = True
    user.is_verified = True
    await log_audit_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="otp_verified",
        resource_type="auth",
    )
    await db.commit()
    return user


async def check_password_history(db: AsyncSession, user: User, new_password: str) -> bool:
    result = await db.execute(
        select(PasswordHistory.hashed_password)
        .where(
            PasswordHistory.user_id == user.id,
            PasswordHistory.organization_id == user.organization_id,
        )
        .order_by(desc(PasswordHistory.created_at))
        .limit(5)
    )
    recent_hashes = list(result.scalars().all())
    recent_hashes.insert(0, user.hashed_password)
    return security_check_password_history(new_password, recent_hashes, limit=5)


async def change_user_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> None:
    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password confirmation does not match")
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    valid, errors = validate_password_strength(new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
    if await check_password_history(db, user, new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password was recently used")

    db.add(
        PasswordHistory(
            organization_id=user.organization_id,
            user_id=user.id,
            hashed_password=user.hashed_password,
        )
    )
    user.hashed_password = hash_password(new_password)
    user.must_change_password = False
    user.is_first_login = False
    user.password_changed_at = datetime.now(timezone.utc)
    await log_audit_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="password_changed",
        resource_type="auth",
    )
    await db.commit()


async def enforce_30_day_password_expiry(user: User) -> None:
    if user.password_changed_at is None:
        user.must_change_password = True
        return
    changed_at = user.password_changed_at
    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)
    if changed_at + timedelta(days=PASSWORD_EXPIRY_DAYS) <= datetime.now(timezone.utc):
        user.must_change_password = True


async def generate_password_reset_token(db: AsyncSession, user: User) -> str:
    token = secrets.token_urlsafe(48)
    await db.execute(
        update(OTPVerification)
        .where(
            OTPVerification.user_id == user.id,
            OTPVerification.organization_id == user.organization_id,
            OTPVerification.otp_type == "password_reset",
            OTPVerification.is_used.is_(False),
        )
        .values(is_used=True)
    )
    db.add(
        OTPVerification(
            organization_id=user.organization_id,
            user_id=user.id,
            otp_code=token,
            otp_type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )
    )
    await db.flush()
    return token


async def validate_password_reset_token(db: AsyncSession, reset_token: str) -> tuple[User, OTPVerification]:
    result = await db.execute(
        select(OTPVerification, User)
        .join(User, User.id == OTPVerification.user_id)
        .where(
            OTPVerification.otp_code == reset_token,
            OTPVerification.otp_type == "password_reset",
            OTPVerification.is_used.is_(False),
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    otp, user = row
    if is_otp_expired(otp.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    return user, otp
