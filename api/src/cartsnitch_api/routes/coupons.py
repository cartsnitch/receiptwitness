"""Coupon routes: browse, relevant matches."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import CouponResponse
from cartsnitch_api.services.coupons import CouponService

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.get("", response_model=list[CouponResponse])
async def list_coupons(
    store_id: UUID | None = Query(None),
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CouponService(db)
    return await svc.list_coupons(store_id)


@router.get("/relevant", response_model=list[CouponResponse])
async def relevant_coupons(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CouponService(db)
    return await svc.relevant_coupons(user_id)
