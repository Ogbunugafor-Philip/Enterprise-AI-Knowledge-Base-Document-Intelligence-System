from typing import Annotated

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.email import send_otp_verification_email, send_password_reset_email
from app.core.security import hash_password, validate_password_strength
from app.models.auth import PasswordHistory
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    OTPVerifyRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserResponse,
)
from app.services.auth_service import (
    change_user_password,
    check_password_history,
    create_otp_for_user,
    generate_password_reset_token,
    log_audit_event,
    validate_password_reset_token,
    verify_user_otp,
    authenticate_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        organization_id=user.organization_id,
        department_id=user.department_id,
        role=user.role.name if user.role else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_first_login=user.is_first_login,
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> LoginResponse:
    user, token = await authenticate_user(db, payload.email, payload.password)
    return LoginResponse(
        access_token=token,
        user=_user_response(user),
        must_change_password=user.must_change_password or user.is_first_login,
    )


@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(payload: OTPVerifyRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> MessageResponse:
    await verify_user_otp(db, payload.email, payload.otp_code)
    return MessageResponse(message="OTP verified successfully")


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(payload: PasswordResetRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> MessageResponse:
    result = await db.execute(select(User).where(User.email == payload.email).order_by(User.created_at))
    user = result.scalars().first()
    if user is not None:
        otp = await create_otp_for_user(db, user, otp_type="verification")
        await send_otp_verification_email(user.email, otp.otp_code)
        await log_audit_event(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            action="otp_resent",
            resource_type="auth",
        )
        await db.commit()
    return MessageResponse(message="If the account exists, a verification code has been sent")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await change_user_password(
        db,
        current_user,
        payload.current_password,
        payload.new_password,
        payload.confirm_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    result = await db.execute(select(User).where(User.email == payload.email).order_by(User.created_at))
    user = result.scalars().first()
    if user is not None:
        token = await generate_password_reset_token(db, user)
        await send_password_reset_email(user.email, token)
        await log_audit_event(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            action="password_reset_requested",
            resource_type="auth",
        )
        await db.commit()
    return MessageResponse(message="If the account exists, password reset instructions have been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password confirmation does not match")
    valid, errors = validate_password_strength(payload.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)

    user, token = await validate_password_reset_token(db, payload.reset_token)
    if await check_password_history(db, user, payload.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password was recently used")

    db.add(
        PasswordHistory(
            organization_id=user.organization_id,
            user_id=user.id,
            hashed_password=user.hashed_password,
        )
    )
    user.hashed_password = hash_password(payload.new_password)
    user.must_change_password = False
    user.is_first_login = False
    user.password_changed_at = datetime.now(timezone.utc)
    token.is_used = True
    await log_audit_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="password_reset_completed",
        resource_type="auth",
    )
    await db.commit()
    return MessageResponse(message="Password reset successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await log_audit_event(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="logout",
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_active_user)]) -> UserResponse:
    return _user_response(current_user)
