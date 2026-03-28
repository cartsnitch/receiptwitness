"""Coupon service — browse coupons, find relevant ones."""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class CouponService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_coupons(self, store_id: UUID | None = None) -> list[dict]:
        from cartsnitch_api.models import Coupon

        today = date.today()
        query = (
            select(Coupon)
            .where((Coupon.valid_to >= today) | (Coupon.valid_to.is_(None)))
            .options(selectinload(Coupon.store))
            .order_by(Coupon.valid_to.asc().nullslast())
        )
        if store_id:
            query = query.where(Coupon.store_id == store_id)

        result = await self.db.execute(query)
        coupons = result.scalars().all()
        return [self._to_dict(c) for c in coupons]

    async def relevant_coupons(self, user_id: UUID) -> list[dict]:
        """Coupons for products the user has purchased."""
        from cartsnitch_api.models import Coupon, PurchaseItem

        today = date.today()

        # Get product IDs from user's purchase history
        from cartsnitch_api.models import Purchase

        items_result = await self.db.execute(
            select(PurchaseItem.normalized_product_id)
            .join(Purchase)
            .where(
                Purchase.user_id == user_id,
                PurchaseItem.normalized_product_id.isnot(None),
            )
            .distinct()
        )
        product_ids = [row[0] for row in items_result.all()]

        if not product_ids:
            return []

        result = await self.db.execute(
            select(Coupon)
            .where(
                Coupon.normalized_product_id.in_(product_ids),
                (Coupon.valid_to >= today) | (Coupon.valid_to.is_(None)),
            )
            .options(selectinload(Coupon.store))
        )
        coupons = result.scalars().all()
        return [self._to_dict(c) for c in coupons]

    def _to_dict(self, c) -> dict:
        return {
            "id": c.id,
            "store_id": c.store_id,
            "store_name": c.store.name,
            "description": c.description or c.title,
            "discount_value": float(c.discount_value) if c.discount_value else 0,
            "discount_type": c.discount_type,
            "product_id": c.normalized_product_id,
            "expires_at": c.valid_to,
        }
