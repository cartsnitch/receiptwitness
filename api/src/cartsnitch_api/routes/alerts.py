"""Alert routes: list alerts, manage settings."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import AlertResponse, AlertSettingsRequest, AlertSettingsResponse
from cartsnitch_api.services.alerts import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AlertService(db)
    return await svc.list_alerts(user_id)


@router.get("/settings", response_model=AlertSettingsResponse)
async def get_alert_settings(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AlertService(db)
    return await svc.get_settings(user_id)


@router.put("/settings")
async def update_alert_settings(
    body: AlertSettingsRequest,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Alert settings persistence not yet implemented. "
        "Use GET /alerts/settings for current defaults.",
    )
