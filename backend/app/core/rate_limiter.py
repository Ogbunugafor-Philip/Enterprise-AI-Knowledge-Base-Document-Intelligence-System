import time
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from starlette.responses import JSONResponse

from app.core.config import settings


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int = 0


class RateLimiter:
    def __init__(self, redis_client=None) -> None:
        self.redis = redis_client
        self._memory: dict[str, tuple[int, int]] = {}

    def _window(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = int(time.time())
        bucket = now // window_seconds
        store_key = f"{key}:{bucket}"
        reset_at = (bucket + 1) * window_seconds

        count = None
        if self.redis is not None:
            try:
                count = int(self.redis.incr(store_key))
                if count == 1:
                    self.redis.expire(store_key, window_seconds)
            except Exception:
                count = None
        if count is None:
            current_count, current_reset = self._memory.get(store_key, (0, reset_at))
            if current_reset <= now:
                current_count = 0
                current_reset = reset_at
            count = current_count + 1
            self._memory[store_key] = (count, current_reset)

        remaining = max(0, limit - count)
        allowed = count <= limit
        return RateLimitResult(allowed, limit, remaining, reset_at, max(0, reset_at - now))

    def _raise_if_limited(self, result: RateLimitResult) -> RateLimitResult:
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(result.retry_after)},
            )
        return result

    def rate_limit_by_ip(self, ip_address: str, limit: int = 100, window_seconds: int = 60) -> RateLimitResult:
        return self._raise_if_limited(self._window(f"ip:{ip_address}", limit, window_seconds))

    def rate_limit_by_user(self, user_id: str, limit: int = 200, window_seconds: int = 60) -> RateLimitResult:
        return self._raise_if_limited(self._window(f"user:{user_id}", limit, window_seconds))

    def rate_limit_by_organization(self, organization_id: str, limit: int | None = None, window_seconds: int = 60) -> RateLimitResult:
        return self._raise_if_limited(self._window(f"org:{organization_id}", limit or settings.API_RATE_LIMIT_PER_ORG or 1000, window_seconds))

    def rate_limit_login(self, ip_address: str, email: str | None = None) -> RateLimitResult:
        ip_result = self._window(f"login:ip:{ip_address}", 10, 15 * 60)
        email_result = self._window(f"login:email:{(email or '').lower()}", 5, 15 * 60) if email else ip_result
        result = ip_result if not ip_result.allowed else email_result
        return self._raise_if_limited(result)

    def rate_limit_file_upload(self, user_id: str, limit: int = 20, window_seconds: int = 3600) -> RateLimitResult:
        return self._raise_if_limited(self._window(f"upload:user:{user_id}", limit, window_seconds))

    def get_rate_limit_status(self, key: str | None = None) -> dict:
        now = int(time.time())
        items = []
        for item_key, (count, reset_at) in self._memory.items():
            if key and key not in item_key:
                continue
            items.append(
                {
                    "key": item_key,
                    "count": count,
                    "reset_at": datetime.fromtimestamp(reset_at, tz=timezone.utc).isoformat(),
                    "expired": reset_at <= now,
                }
            )
        return {"items": items}

    def reset_rate_limit(self, key: str) -> bool:
        removed = False
        for item_key in list(self._memory):
            if key in item_key:
                self._memory.pop(item_key, None)
                removed = True
        if self.redis is not None:
            try:
                for redis_key in self.redis.scan_iter(f"*{key}*"):
                    self.redis.delete(redis_key)
                    removed = True
            except Exception:
                pass
        return removed


def _make_redis_client():
    try:
        import redis as sync_redis
        import os
        client = sync_redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        client.ping()
        return client
    except Exception:
        return None


rate_limiter = RateLimiter(redis_client=_make_redis_client())


def rate_limit_response(result: RateLimitResult) -> JSONResponse:
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
