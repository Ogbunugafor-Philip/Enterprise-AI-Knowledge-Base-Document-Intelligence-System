"""
Redis response cache with per-key TTL settings.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TTL presets (seconds)
# ---------------------------------------------------------------------------

TTL_DASHBOARD_STATS: int = 10
TTL_DOCUMENT_LIST: int = 30
TTL_USER_PROFILE: int = 300
TTL_SAMPLE_QUESTIONS: int = 3600
TTL_ORGANIZATION_SETTINGS: int = 600
TTL_MONITORING_METRICS: int = 30


def get_redis_url() -> str:
    from app.core.config import settings
    return settings.REDIS_URL


async def get_redis_client():
    """FastAPI dependency — returns a Redis client or None if unavailable."""
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(get_redis_url(), decode_responses=True, socket_connect_timeout=1)
        await client.ping()
        return client
    except Exception:
        return None


class CacheManager:
    """Thin async wrapper around a redis.asyncio client."""

    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    async def cache_response(self, key: str, value: Any, ttl: int) -> None:
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as exc:
            logger.warning("Cache write failed for %s: %s", key, exc)

    async def get_cached_response(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Cache read failed for %s: %s", key, exc)
            return None

    async def invalidate_cache(self, pattern: str) -> int:
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            return len(keys)
        except Exception as exc:
            logger.warning("Cache invalidation failed for %s: %s", pattern, exc)
            return 0

    async def invalidate_organization_cache(self, organization_id: str) -> int:
        return await self.invalidate_cache(f"org:{organization_id}:*")


def make_cache_key(namespace: str, organization_id: str | None, *parts: str) -> str:
    org_part = organization_id or "global"
    suffix = ":".join(str(p) for p in parts) if parts else ""
    return f"org:{org_part}:{namespace}:{suffix}".rstrip(":")
