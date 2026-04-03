"""Purchase routes: list, detail, stats."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import PurchaseDetailResponse, PurchaseResponse, PurchaseStatsResponse
from cartsnitch_api.services.purchases import PurchaseService

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get("", response_model=list[PurchaseResponse])
async def list_purchases(
    user_id: UUID = Depends(get_current_user),
    store_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = PurchaseService(db)
    return await svc.list_purchases(user_id, store_id, page, page_size)


@router.get("/stats", response_model=PurchaseStatsResponse)
async def purchase_stats(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PurchaseService(db)
    return await svc.get_stats(user_id)


@router.get("/{purchase_id}", response_model=PurchaseDetailResponse)
async def get_purchase(
    purchase_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PurchaseService(db)
    try:
        return await svc.get_purchase(purchase_id, user_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found"
        ) from None
