"""Rate limiting middleware for public and authenticated endpoints.

Uses in-memory sliding window as fallback, Redis/DragonflyDB when available.
Per-IP limiting on public endpoints, per-token limiting on authenticated endpoints.
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from cartsnitch_api.config import settings


class _SlidingWindowCounter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, retry_after)."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            # Prune expired entries
            self._hits[key] = [t for t in self._hits[key] if t > cutoff]

            current_count = len(self._hits[key])
            if current_count >= self.max_requests:
                retry_after = int(self._hits[key][0] - cutoff) + 1
                return False, 0, retry_after

            self._hits[key].append(now)
            remaining = self.max_requests - current_count - 1
            return True, remaining, 0


# Module-level counters — one for public (per-IP), one for auth (per-token)
_public_limiter = _SlidingWindowCounter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
_auth_limiter = _SlidingWindowCounter(
    max_requests=settings.rate_limit_requests * 5,  # 300/min for authenticated users
    window_seconds=settings.rate_limit_window_seconds,
)


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_rate_limit_key(request: Request) -> tuple[str, _SlidingWindowCounter]:
    """Determine rate limit key and which limiter to use."""
    if request.url.path.startswith("/public"):
        return f"ip:{_get_client_ip(request)}", _public_limiter

    # For authenticated endpoints, use Bearer token as key if present
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        # Use last 16 chars of token as key to avoid storing full tokens
        return f"token:{token[-16:]}", _auth_limiter

    # Fallback to IP for unauthenticated non-public endpoints
    return f"ip:{_get_client_ip(request)}", _public_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting when disabled (e.g. in tests) or for health checks
        if not settings.rate_limit_enabled or request.url.path == "/health":
            return await call_next(request)

        key, limiter = _get_rate_limit_key(request)
        allowed, remaining, retry_after = limiter.is_allowed(key)

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
