"""Price routes: trends, increases, comparison."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import (
    PriceComparisonResponse,
    PriceIncreaseResponse,
    PriceTrendResponse,
)
from cartsnitch_api.services.prices import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/trends", response_model=list[PriceTrendResponse])
async def price_trends(
    user_id: str = Depends(get_current_user),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = PriceService(db)
    return await svc.get_trends(category)


@router.get("/increases", response_model=list[PriceIncreaseResponse])
async def price_increases(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PriceService(db)
    return await svc.get_increases()


@router.get("/comparison", response_model=list[PriceComparisonResponse])
async def price_comparison(
    product_ids: Annotated[list[UUID], Query()],
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PriceService(db)
    return await svc.get_comparison(product_ids)
