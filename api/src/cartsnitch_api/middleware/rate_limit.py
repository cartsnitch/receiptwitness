"""Rate limiting middleware for public and authenticated endpoints.

Uses in-memory sliding window as fallback, Redis/DragonflyDB when available.
Per-IP limiting on public endpoints, per-token limiting on authenticated endpoints.
"""

import hashlib
import logging
import time
import uuid
from collections import defaultdict
from threading import Lock
from typing import Protocol

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis, RedisError
from starlette.middleware.base import BaseHTTPMiddleware

from cartsnitch_api.config import settings

logger = logging.getLogger(__name__)


class RateLimitBackend(Protocol):
    """Protocol for rate limit backends."""

    async def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, retry_after)."""


class InMemorySlidingWindow:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    async def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, retry_after)."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            self._hits[key] = [t for t in self._hits[key] if t > cutoff]

            current_count = len(self._hits[key])
            if current_count >= self.max_requests:
                retry_after = int(self._hits[key][0] - cutoff) + 1
                return False, 0, retry_after

            self._hits[key].append(now)
            remaining = self.max_requests - current_count - 1
            return True, remaining, 0


class RedisSlidingWindow:
    """Redis-backed sliding window rate limiter using sorted sets."""

    def __init__(self, redis: Redis, max_requests: int, window_seconds: int) -> None:
        self.redis = redis
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, retry_after)."""
        try:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            now_ms = int(now * 1000)
            cutoff_ms = int(cutoff * 1000)

            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, cutoff_ms)
            pipe.zcard(key)
            results = await pipe.execute()

            current_count = results[1]

            if current_count >= self.max_requests:
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int((oldest[0][1] - cutoff) / 1000) + 1
                else:
                    retry_after = self.window_seconds
                return False, 0, retry_after

            member = f"{now_ms}:{uuid.uuid4().hex[:8]}"
            pipe = self.redis.pipeline()
            pipe.zadd(key, {member: now_ms})
            pipe.expire(key, self.window_seconds)
            await pipe.execute()

            remaining = self.max_requests - current_count - 1
            return True, remaining, 0

        except RedisError as e:
            logger.warning("Redis rate limit error, falling back to in-memory: %s", e)
            in_memory = InMemorySlidingWindow(self.max_requests, self.window_seconds)
            return await in_memory.is_allowed(key)


_redis_client: Redis | None = None
_use_redis = False

if settings.rate_limit_redis_enabled:
    try:
        _redis_client = Redis.from_url(settings.redis_url)
        _use_redis = True
        logger.info("Rate limiting will use Redis at %s", settings.redis_url)
    except Exception as e:
        logger.warning("Failed to connect to Redis for rate limiting, using in-memory: %s", e)
        _use_redis = False

if _use_redis and _redis_client:
    _public_limiter = RedisSlidingWindow(
        _redis_client, settings.rate_limit_requests, settings.rate_limit_window_seconds
    )
    _auth_limiter = RedisSlidingWindow(
        _redis_client, settings.rate_limit_requests * 5, settings.rate_limit_window_seconds
    )
    _auth_strict_limiter = RedisSlidingWindow(
        _redis_client, settings.rate_limit_auth_requests, settings.rate_limit_auth_window_seconds
    )
else:
    _public_limiter = InMemorySlidingWindow(
        settings.rate_limit_requests, settings.rate_limit_window_seconds
    )
    _auth_limiter = InMemorySlidingWindow(
        settings.rate_limit_requests * 5, settings.rate_limit_window_seconds
    )
    _auth_strict_limiter = InMemorySlidingWindow(
        settings.rate_limit_auth_requests, settings.rate_limit_auth_window_seconds
    )


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_rate_limit_key(request: Request) -> tuple[str, RateLimitBackend]:
    """Determine rate limit key and which limiter to use."""
    if request.url.path.startswith("/public"):
        return f"ip:{_get_client_ip(request)}", _public_limiter

    if request.url.path.startswith("/auth/") and request.method == "POST":
        return f"ip:{_get_client_ip(request)}", _auth_strict_limiter

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"token:{token_hash}", _auth_limiter

    return f"ip:{_get_client_ip(request)}", _public_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or request.url.path == "/health":
            return await call_next(request)

        key, limiter = _get_rate_limit_key(request)
        allowed, remaining, retry_after = await limiter.is_allowed(key)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "code": "RATE_LIMITED",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def add_rate_limit_middleware(app: FastAPI) -> None:
    app.add_middleware(RateLimitMiddleware)
