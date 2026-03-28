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
async def public_price_trend(product_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = PublicService(db)
    try:
        return await svc.get_trend(product_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        ) from None


@router.get("/store-comparison", response_model=PublicStoreComparisonResponse)
async def public_store_comparison(
    product_ids: Annotated[list[UUID], Query(max_length=20)],
    db: AsyncSession = Depends(get_db),
):
    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one product_id is required",
        )
    svc = PublicService(db)
    return await svc.get_store_comparison(product_ids)


@router.get("/inflation", response_model=PublicInflationResponse)
async def public_inflation(db: AsyncSession = Depends(get_db)):
    svc = PublicService(db)
    return await svc.get_inflation()
