import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.core.permissions import RoleEnum
from app.models.user import User

router = APIRouter(tags=["health"])


async def _check_database(db: AsyncSession) -> dict:
    start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "response_time_ms": round((time.monotonic() - start) * 1000, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc), "response_time_ms": round((time.monotonic() - start) * 1000, 2)}


async def _check_redis() -> dict:
    start = time.monotonic()
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        await client.ping()
        await client.aclose()
        return {"status": "ok", "response_time_ms": round((time.monotonic() - start) * 1000, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc), "response_time_ms": round((time.monotonic() - start) * 1000, 2)}


async def _check_qdrant() -> dict:
    start = time.monotonic()
    try:
        import httpx
        qdrant_host = os.getenv("QDRANT_HOST", settings.QDRANT_HOST)
        qdrant_port = settings.QDRANT_PORT
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"http://{qdrant_host}:{qdrant_port}/healthz")
        ok = resp.status_code == 200
        return {
            "status": "ok" if ok else "error",
            "response_time_ms": round((time.monotonic() - start) * 1000, 2),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc), "response_time_ms": round((time.monotonic() - start) * 1000, 2)}


def _build_base_response() -> dict:
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", settings.ENVIRONMENT),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/live")
async def liveness() -> dict:
    """Kubernetes-style liveness probe — no dependencies checked."""
    return _build_base_response()


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe — verifies database, Redis, and Qdrant are reachable."""
    db_status = await _check_database(db)
    redis_status = await _check_redis()
    qdrant_status = await _check_qdrant()

    services_ok = all(
        s["status"] == "ok" for s in [db_status, redis_status, qdrant_status]
    )

    response = {
        **_build_base_response(),
        "status": "ok" if services_ok else "degraded",
        "services": {
            "database": db_status,
            "redis": redis_status,
            "qdrant": qdrant_status,
        },
    }

    if not services_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response,
        )
    return response


@router.get("/health/detailed")
async def detailed_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Detailed health including disk/memory — requires SUPER_ADMIN."""
    if not current_user.role or current_user.role.name != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    db_status = await _check_database(db)
    redis_status = await _check_redis()
    qdrant_status = await _check_qdrant()

    services_ok = all(
        s["status"] == "ok" for s in [db_status, redis_status, qdrant_status]
    )

    # Disk usage
    import shutil
    disk = shutil.disk_usage("/")
    disk_info = {
        "total_gb": round(disk.total / 1e9, 2),
        "used_gb": round(disk.used / 1e9, 2),
        "free_gb": round(disk.free / 1e9, 2),
        "used_percent": round(disk.used / disk.total * 100, 1),
    }

    # Memory usage
    import resource
    mem = resource.getrusage(resource.RUSAGE_SELF)
    memory_info = {
        "rss_mb": round(mem.ru_maxrss / 1024, 2),
    }

    return {
        **_build_base_response(),
        "status": "ok" if services_ok else "degraded",
        "services": {
            "database": db_status,
            "redis": redis_status,
            "qdrant": qdrant_status,
        },
        "system": {
            "disk": disk_info,
            "memory": memory_info,
        },
    }
