"""Structured error responses and error monitoring.

Ensures all errors return a consistent JSON shape and never leak stack traces.
Provides hooks for error monitoring/alerting.
"""

import logging
import time
import traceback
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("cartsnitch_api.errors")


def _error_response(
    status_code: int,
    detail: str,
    code: str | None = None,
    errors: list[dict] | None = None,
) -> JSONResponse:
    """Build a consistent error response."""
    body: dict = {"detail": detail}
    if code:
        body["code"] = code
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body)


def add_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent error responses."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return 422 with structured field-level error details."""
        field_errors = []
        for err in exc.errors():
            loc = err.get("loc", ())
            field_errors.append(
                {
                    "field": ".".join(str(p) for p in loc[1:]) if len(loc) > 1 else str(loc),
                    "message": err.get("msg", "Invalid value"),
                    "type": err.get("type", "value_error"),
                }
            )
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error",
            code="VALIDATION_ERROR",
            errors=field_errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Wrap HTTP exceptions (Starlette and FastAPI) in consistent format."""
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return _error_response(
            status_code=exc.status_code,
            detail=detail,
            code=_status_to_code(exc.status_code),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all: log full traceback, return safe 500 to client."""
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            exc,
            traceback.format_exc(),
        )
        _notify_error_monitor(request, exc)

        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
            code="INTERNAL_ERROR",
        )


def _status_to_code(status_code: int) -> str:
    """Map HTTP status code to a machine-readable error code."""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


# ---------- Error Monitoring ----------


class _ErrorMonitor:
    """Simple error counter for monitoring and alerting hooks.

    Tracks error counts and rates. In production, this would forward
    to an external monitoring service (Prometheus, Sentry, etc.).
    """

    def __init__(self) -> None:
        self.error_counts: dict[int, int] = {}
        self.recent_5xx: list[dict] = []
        self._max_recent = 100

    def record(self, status_code: int, path: str, method: str, error: str | None = None) -> None:
        self.error_counts[status_code] = self.error_counts.get(status_code, 0) + 1

        if status_code >= 500:
            entry = {
                "timestamp": time.time(),
                "status": status_code,
                "path": path,
                "method": method,
                "error": error,
            }
            self.recent_5xx.append(entry)
            if len(self.recent_5xx) > self._max_recent:
                self.recent_5xx = self.recent_5xx[-self._max_recent :]

            logger.warning(
                "5xx error recorded: %s %s -> %d (%s)",
                method,
                path,
                status_code,
                error or "unknown",
            )

    def get_stats(self) -> dict:
        return {
            "error_counts": dict(self.error_counts),
            "recent_5xx_count": len(self.recent_5xx),
        }


_monitor = _ErrorMonitor()


def get_error_monitor() -> _ErrorMonitor:
    """Access the global error monitor (for health/metrics endpoints)."""
    return _monitor


def _notify_error_monitor(request: Request, exc: Exception) -> None:
    """Record unhandled exception in the error monitor."""
    _monitor.record(
        status_code=500,
        path=request.url.path,
        method=request.method,
        error=str(exc)[:200],
    )


class ErrorMonitorMiddleware(BaseHTTPMiddleware):
    """Middleware to track all 4xx/5xx responses for monitoring."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        response = await call_next(request)

        if response.status_code >= 400:
            _monitor.record(
                status_code=response.status_code,
                path=request.url.path,
                method=request.method,
            )

        return response


def add_error_monitor_middleware(app: FastAPI) -> None:
    app.add_middleware(ErrorMonitorMiddleware)
