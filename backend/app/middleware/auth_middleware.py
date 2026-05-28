from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

PUBLIC_PATH_PREFIXES = (
    "/",
    "/api/health",
    "/api/v1/tenancy/status",
    "/api/v1/auth/login",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/resend-otp",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _is_public_path(path: str) -> bool:
    if path == "/":
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES if prefix != "/")


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if _is_public_path(request.url.path):
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                {"detail": "Missing authentication token"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        token = authorization.removeprefix("Bearer ").strip()
        try:
            payload = decode_access_token(token)
            user_id = UUID(str(payload["sub"]))
            organization_id = UUID(str(payload["organization_id"]))
        except Exception:
            return JSONResponse(
                {"detail": "Invalid authentication token"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        async with SessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id, User.organization_id == organization_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                return JSONResponse({"detail": "User not found"}, status_code=status.HTTP_401_UNAUTHORIZED)
            if not user.is_active or not user.is_verified:
                return JSONResponse({"detail": "Insufficient permissions"}, status_code=status.HTTP_403_FORBIDDEN)
            request.state.user = user
            request.state.organization_id = user.organization_id

        return await call_next(request)


class PasswordExpiryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        user = getattr(request.state, "user", None)
        if user is not None:
            changed_at = user.password_changed_at
            password_expired = changed_at is None
            if changed_at is not None:
                if changed_at.tzinfo is None:
                    changed_at = changed_at.replace(tzinfo=timezone.utc)
                password_expired = changed_at + timedelta(days=30) <= datetime.now(timezone.utc)
            request.state.password_reset_required = bool(user.must_change_password or password_expired)
        return await call_next(request)
