"""Health check and error metrics endpoints."""

from fastapi import APIRouter, Depends

from cartsnitch_api.auth.dependencies import verify_service_key
from cartsnitch_api.middleware.error_handler import get_error_monitor

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/internal/error-stats", dependencies=[Depends(verify_service_key)])
async def error_stats():
    """Error monitoring stats — internal only (requires X-Service-Key)."""
    monitor = get_error_monitor()
    return monitor.get_stats()
