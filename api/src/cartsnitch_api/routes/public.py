"""Public endpoints: price transparency data (no auth required)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import (
    PublicInflationResponse,
    PublicStoreComparisonResponse,
    PublicTrendResponse,
)
from cartsnitch_api.services.public import PublicService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/trends/{product_id}", response_model=PublicTrendResponse)
async def public_price_trend(
    product_id: UUID,
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    svc = PublicService(db)
    try:
        return await svc.get_trend(product_id, days=days)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        ) from None


@router.get("/store-comparison", response_model=PublicStoreComparisonResponse)
async def public_store_comparison(
    product_ids: Annotated[list[UUID], Query(max_length=20)],
    category: str | None = Query(None, max_length=100, pattern=r"^[a-zA-Z0-9 _-]+$"),
    db: AsyncSession = Depends(get_db),
):
    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one product_id is required",
        )
    svc = PublicService(db)
    return await svc.get_store_comparison(product_ids, category=category)


@router.get("/inflation", response_model=PublicInflationResponse)
async def public_inflation(
    category: str | None = Query(None, max_length=100, pattern=r"^[a-zA-Z0-9 _-]+$"),
    period: str = Query("all-time", pattern=r"^(all-time|1y|6m|3m|1m)$"),
    db: AsyncSession = Depends(get_db),
):
    svc = PublicService(db)
    return await svc.get_inflation(category=category, period=period)
