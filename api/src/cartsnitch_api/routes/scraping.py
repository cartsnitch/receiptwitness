"""Scraping routes: trigger sync, check status (proxy to ReceiptWitness)."""

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError, RequestError

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.schemas import SyncStatusResponse, SyncTriggerResponse
from cartsnitch_api.services.receiptwitness import ReceiptWitnessClient

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/{store_slug}/sync", response_model=SyncTriggerResponse)
async def trigger_sync(store_slug: str, user_id: str = Depends(get_current_user)):
    client = ReceiptWitnessClient()
    try:
        result = await client.trigger_sync(str(user_id), store_slug)
        return result
    except HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail="Sync service error",
        ) from e
    except RequestError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach sync service",
        ) from None


@router.get("/status", response_model=list[SyncStatusResponse])
async def sync_status(user_id: str = Depends(get_current_user)):
    client = ReceiptWitnessClient()
    try:
        return await client.get_sync_status(str(user_id))
    except (HTTPStatusError, RequestError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach sync service",
        ) from None
