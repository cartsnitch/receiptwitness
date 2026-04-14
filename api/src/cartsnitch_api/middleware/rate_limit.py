"""Rate limiting middleware for public and authenticated endpoints.

Uses in-memory sliding window as fallback, Redis/DragonflyDB when available.
Per-IP limiting on public endpoints, per-token limiting on authenticated endpoints.
"""

import asyncio
import hashlib
import logging
import time
import uuid
from collections import defaultdict
from threading import Lock
from typing import Protocol, runtime_checkable

import redis.asyncio as redis
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from cartsnitch_api.config import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class RateLimiter(Protocol):
    """Protocol for rate limiter implementations."""

    async def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, retry_after)."""
        ...


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

    def __init__(self, client: redis.Redis, max_requests: int, window_seconds: int) -> None:
        self.client = client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed using Redis sorted sets. Returns (allowed, remaining, retry_after)."""
        now_ms = int(time.time() * 1000)
        window_ms = self.window_seconds * 1000
        cutoff = now_ms - window_ms

        try:
            async with self.client.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zcard(key)
                await pipe.execute()

            current_count = await self.client.zcard(key)

            if current_count >= self.max_requests:
                results = await self.client.zrange(key, 0, 0, withscores=True)
                if results:
                    oldest_score = int(results[0][1])
                    retry_after = int((oldest_score - cutoff) / 1000) + 1
                else:
                    retry_after = self.window_seconds
                return False, 0, retry_after

            member = f"{now_ms}:{uuid.uuid4().hex[:8]}"
            async with self.client.pipeline(transaction=True) as pipe:
                pipe.zadd(key, {member: now_ms})
                pipe.expire(key, self.window_seconds)
                await pipe.execute()

            remaining = self.max_requests - current_count - 1
            return True, remaining, 0

        except Exception as e:
            logger.warning(f"Redis rate limit error, falling back to in-memory: {e}")
            raise


_redis_client: redis.Redis | None = None
_use_redis = False


def _get_limiters() -> tuple[RateLimiter, RateLimiter, RateLimiter]:
    """Get the three rate limiters (public, auth, auth_strict)."""
    global _redis_client, _use_redis

    if _use_redis and _redis_client is not None:
        return (
            RedisSlidingWindow(
                _redis_client, settings.rate_limit_requests, settings.rate_limit_window_seconds
            ),
            RedisSlidingWindow(
                _redis_client, settings.rate_limit_requests * 5, settings.rate_limit_window_seconds
            ),
            RedisSlidingWindow(
                _redis_client,
                settings.rate_limit_auth_requests,
                settings.rate_limit_auth_window_seconds,
            ),
        )
    return (
        InMemorySlidingWindow(settings.rate_limit_requests, settings.rate_limit_window_seconds),
        InMemorySlidingWindow(settings.rate_limit_requests * 5, settings.rate_limit_window_seconds),
        InMemorySlidingWindow(
            settings.rate_limit_auth_requests, settings.rate_limit_auth_window_seconds
        ),
    )


def _init_redis() -> None:
    """Initialize Redis connection at module load."""
    global _redis_client, _use_redis

    if not settings.rate_limit_redis_enabled:
        logger.info("Redis rate limiting disabled via config")
        return

    try:
        _redis_client = redis.from_url(settings.redis_url)
        asyncio.get_event_loop().run_until_complete(_redis_client.ping())
        _use_redis = True
        logger.info("Redis rate limiting enabled")
    except Exception as e:
        logger.warning(f"Redis unavailable for rate limiting, using in-memory: {e}")
        _use_redis = False


_init_redis()


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_rate_limit_key(request: Request) -> tuple[str, RateLimiter]:
    """Determine rate limit key and which limiter to use."""
    public_limiter, auth_limiter, auth_strict_limiter = _get_limiters()

    if request.url.path.startswith("/public"):
        return f"ip:{_get_client_ip(request)}", public_limiter

    if request.url.path.startswith("/auth/") and request.method == "POST":
        return f"ip:{_get_client_ip(request)}", auth_strict_limiter

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"token:{token_hash}", auth_limiter

    return f"ip:{_get_client_ip(request)}", public_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or request.url.path == "/health":
            return await call_next(request)

        key, limiter = _get_rate_limit_key(request)

        try:
            allowed, remaining, retry_after = await limiter.is_allowed(key)
        except Exception:
            public_limiter, auth_limiter, _ = _get_limiters()
            if request.url.path.startswith("/auth/") and request.method == "POST":
                limiter = auth_limiter
            elif request.url.path.startswith("/public"):
                limiter = public_limiter
            elif request.headers.get("authorization", "").startswith("Bearer "):
                limiter = auth_limiter
            else:
                limiter = public_limiter
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
