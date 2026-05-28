import re
import os
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_REQUEST_SIZE = 100 * 1024 * 1024
SQL_PATTERNS = (
    re.compile(r"\bUNION\s+SELECT\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bINSERT\s+INTO\b", re.IGNORECASE),
    re.compile(r"\bOR\s+1\s*=\s*1\b", re.IGNORECASE),
    re.compile(r"--"),
    re.compile(r"\bxp_cmdshell\b", re.IGNORECASE),
)
SUSPICIOUS_HEADERS = ("x-forwarded-host", "x-original-url", "x-rewrite-url")


async def _log_security_event(request: Request, event_type: str, description: str, severity: str = "HIGH") -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    try:
        from app.core.database import SessionLocal
        from app.models.monitoring import MonitoringLog, SystemAlert

        organization_id = getattr(request.state, "organization_id", None)
        async with SessionLocal() as db:
            if organization_id is not None:
                db.add(
                    MonitoringLog(
                        organization_id=organization_id,
                        event_type=event_type,
                        service_name="security",
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=400,
                        error_message=description,
                        ip_address=request.client.host if request.client else None,
                        token_usage={"severity": severity},
                    )
                )
                if event_type == "sql_injection":
                    db.add(
                        SystemAlert(
                            organization_id=organization_id,
                            alert_type="sql_injection_attempt",
                            severity="high",
                            title="SQL injection attempt detected",
                            description=description,
                            affected_service="api",
                            recommended_action="Review source IP, endpoint, and request payload.",
                            business_impact="Potential attempt to access or modify tenant data.",
                        )
                    )
                await db.commit()
    except Exception:
        pass


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            await _log_security_event(request, "request_too_large", "Request exceeded 100MB", "HIGH")
            return JSONResponse({"detail": "Request too large"}, status_code=413)

        if request.method in {"POST", "PUT"}:
            content_type = request.headers.get("content-type", "")
            if content_type and not (
                content_type.startswith("application/json")
                or content_type.startswith("multipart/form-data")
                or content_type.startswith("application/x-www-form-urlencoded")
            ):
                await _log_security_event(request, "invalid_content_type", content_type, "HIGH")
                return JSONResponse({"detail": "Unsupported content type"}, status_code=415)

        for header in SUSPICIOUS_HEADERS:
            if request.headers.get(header):
                await _log_security_event(request, "suspicious_header", f"Suspicious header: {header}", "HIGH")
                return JSONResponse({"detail": "Suspicious request header"}, status_code=400)

        return await call_next(request)


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def contains_sql_injection(value: str) -> bool:
        return any(pattern.search(value or "") for pattern in SQL_PATTERNS)

    async def dispatch(self, request: Request, call_next) -> Response:
        inspected = [request.url.path]
        inspected.extend(str(value) for value in request.query_params.values())
        inspected.extend(str(key) for key in request.query_params.keys())
        for value in inspected:
            if self.contains_sql_injection(value):
                await _log_security_event(request, "sql_injection", f"SQL injection pattern detected: {value[:200]}", "HIGH")
                return JSONResponse({"detail": "Invalid request parameters"}, status_code=400)
        return await call_next(request)
