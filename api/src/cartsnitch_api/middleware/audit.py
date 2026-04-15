"""Audit logging middleware for sensitive API operations.

Logs structured JSON for POST/PUT/PATCH/DELETE requests and GET /auth/me.
Never logs request bodies, response bodies, Authorization headers, or cookie values.
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("cartsnitch_api.audit")

HEALTH_PATHS = {"/health", "/healthz", "/ready"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log structured audit events for sensitive operations."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        if request.method == "OPTIONS" or request.url.path in HEALTH_PATHS:
            return await call_next(request)

        method = request.method
        path = request.url.path

        is_sensitive_write = method in {"POST", "PUT", "PATCH", "DELETE"}
        is_auth_me_read = method == "GET" and path == "/auth/me"

        if not (is_sensitive_write or is_auth_me_read):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        user_id = getattr(request.state, "user_id", None)
        client_ip = request.client.host if request.client else "unknown"

        log_entry = {
            "event": "audit",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_id": user_id,
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        logger.info(json.dumps(log_entry))

        return response


def add_audit_middleware(app: FastAPI) -> None:
    app.add_middleware(AuditMiddleware)
