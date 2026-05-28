from datetime import datetime, timezone
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.database import SessionLocal
from app.core.permissions import ROLE_PERMISSIONS, normalize_role
from app.core.security import decode_access_token
from app.models.monitoring import MonitoringLog

PUBLIC_PATH_PREFIXES = (
    "/",
    "/api/health",
    "/health",
    "/api/v1/tenancy/status",
    "/api/v1/auth/login",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/resend-otp",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/setup/super-admin",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def is_public_path(path: str) -> bool:
    if path == "/":
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES if prefix != "/")


class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if is_public_path(request.url.path):
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse({"detail": "Authentication required"}, status_code=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = decode_access_token(authorization.removeprefix("Bearer ").strip())
            role = normalize_role(payload.get("role"))
            organization_id = UUID(str(payload["organization_id"])) if payload.get("organization_id") else None
            user_id = UUID(str(payload["sub"]))
        except Exception:
            return JSONResponse({"detail": "Invalid authentication token"}, status_code=status.HTTP_401_UNAUTHORIZED)

        if role is None:
            return JSONResponse({"detail": "Insufficient permissions"}, status_code=status.HTTP_403_FORBIDDEN)

        request.state.role = role
        request.state.permissions = ROLE_PERMISSIONS[role]
        request.state.organization_id = organization_id
        request.state.user_id = user_id

        response = await call_next(request)
        async with SessionLocal() as db:
            db.add(
                MonitoringLog(
                    organization_id=organization_id,
                    event_type="access_attempt",
                    service_name="api",
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    response_time_ms=0,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    token_usage={"checked_at": datetime.now(timezone.utc).isoformat()},
                )
            )
            await db.commit()
        return response
