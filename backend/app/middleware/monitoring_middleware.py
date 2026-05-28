import time
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_SKIP_PREFIXES = ("/api/health", "/health", "/docs", "/redoc", "/openapi.json", "/static")


def _should_monitor(path: str) -> bool:
    if path == "/":
        return False
    return not any(path.startswith(p) for p in _SKIP_PREFIXES)


class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not _should_monitor(request.url.path):
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        try:
            organization_id: UUID | None = getattr(request.state, "organization_id", None)
            user_id: UUID | None = getattr(request.state, "user_id", None)
            if organization_id is not None:
                from app.core.database import SessionLocal
                from app.services.monitoring_service import track_api_request

                async with SessionLocal() as db:
                    await track_api_request(
                        db,
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=response.status_code,
                        response_time_ms=elapsed_ms,
                        user_id=user_id,
                        organization_id=organization_id,
                        ip_address=request.client.host if request.client else None,
                    )
                    await db.commit()
        except Exception:
            pass

        return response
