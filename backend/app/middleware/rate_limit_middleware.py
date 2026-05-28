import json
import os

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.rate_limiter import RateLimitResult, rate_limiter


async def _read_login_email(request: Request) -> str | None:
    try:
        body = await request.body()
        if not body:
            return None
        data = json.loads(body.decode("utf-8"))
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive
        return data.get("email")
    except Exception:
        return None


async def _log_rate_limit_violation(request: Request, description: str) -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    try:
        from app.core.database import SessionLocal
        from app.models.monitoring import MonitoringLog, SystemAlert

        organization_id = getattr(request.state, "organization_id", None)
        if organization_id is None:
            return
        async with SessionLocal() as db:
            db.add(
                MonitoringLog(
                    organization_id=organization_id,
                    event_type="rate_limit_exceeded",
                    service_name="security",
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=429,
                    error_message=description,
                    ip_address=request.client.host if request.client else None,
                    token_usage={"severity": "HIGH"},
                )
            )
            db.add(
                SystemAlert(
                    organization_id=organization_id,
                    alert_type="repeated_rate_limit_violation",
                    severity="high",
                    title="Repeated rate limit violation detected",
                    description=description,
                    affected_service="api",
                    recommended_action="Review source IP and consider blocking abusive clients.",
                    business_impact="Service availability may be degraded by abusive traffic.",
                )
            )
            await db.commit()
    except Exception:
        pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    def _limited_response(self, result: RateLimitResult) -> JSONResponse:
        return JSONResponse(
            {"detail": "Rate limit exceeded"},
            status_code=429,
            headers={
                "Retry-After": str(result.retry_after),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_at),
            },
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host if request.client else "unknown"
        applied: RateLimitResult | None = None
        try:
            if request.url.path == "/api/v1/auth/login" and request.method == "POST":
                applied = rate_limiter.rate_limit_login(ip, await _read_login_email(request))
            elif request.url.path.startswith("/api/v1/admin/documents/upload"):
                user_id = getattr(request.state, "user_id", None) or ip
                applied = rate_limiter.rate_limit_file_upload(str(user_id))
            else:
                applied = rate_limiter.rate_limit_by_ip(ip)
                user_id = getattr(request.state, "user_id", None)
                organization_id = getattr(request.state, "organization_id", None)
                if user_id:
                    applied = rate_limiter.rate_limit_by_user(str(user_id))
                if organization_id:
                    applied = rate_limiter.rate_limit_by_organization(str(organization_id))
        except HTTPException as exc:
            retry_after = int((exc.headers or {}).get("Retry-After", "60"))
            result = RateLimitResult(False, 0, 0, retry_after, retry_after)
            await _log_rate_limit_violation(request, f"Rate limit exceeded for {ip} on {request.url.path}")
            return self._limited_response(result)

        response = await call_next(request)
        if applied:
            response.headers["X-RateLimit-Limit"] = str(applied.limit)
            response.headers["X-RateLimit-Remaining"] = str(applied.remaining)
            response.headers["X-RateLimit-Reset"] = str(applied.reset_at)
        return response
