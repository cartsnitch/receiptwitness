"""Public service — unauthenticated price transparency endpoints."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cartsnitch_api.services.queries import latest_price_per_store


class PublicService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_trend(self, product_id: UUID, days: int = 90) -> dict:
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        result = await self.db.execute(
            select(NormalizedProduct).where(NormalizedProduct.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise LookupError("Product not found")

        date_threshold = date.today() - timedelta(days=days)
        prices_result = await self.db.execute(
            select(PriceHistory)
            .where(
                PriceHistory.normalized_product_id == product_id,
                PriceHistory.observed_date >= date_threshold,
            )
            .options(selectinload(PriceHistory.store))
            .order_by(PriceHistory.observed_date)
        )
        prices = prices_result.scalars().all()

        return {
            "product_id": product.id,
            "product_name": product.canonical_name,
            "data_points": [
                {
                    "date": ph.observed_date,
                    "price": float(ph.regular_price),
                    "store_id": ph.store_id,
                    "store_name": ph.store.name,
                }
                for ph in prices
            ],
        }

    async def get_store_comparison(
        self, product_ids: list[UUID], category: str | None = None
    ) -> dict:
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        if not product_ids:
            return {"products": []}

        product_query = select(NormalizedProduct).where(NormalizedProduct.id.in_(product_ids))
        if category:
            product_query = product_query.where(NormalizedProduct.category == category)
        prod_result = await self.db.execute(product_query)
        products_by_id = {p.id: p for p in prod_result.scalars().all()}

        if not products_by_id:
            return {"products": []}

        filtered_product_ids = list(products_by_id.keys())
        subq = latest_price_per_store(filtered_product_ids)
        prices_result = await self.db.execute(
            select(PriceHistory)
            .join(
                subq,
                and_(
                    PriceHistory.store_id == subq.c.store_id,
                    PriceHistory.observed_date == subq.c.max_date,
                    PriceHistory.normalized_product_id == subq.c.normalized_product_id,
                ),
            )
            .where(PriceHistory.normalized_product_id.in_(filtered_product_ids))
            .options(selectinload(PriceHistory.store))
        )
        all_prices = prices_result.scalars().all()

        prices_by_product: dict[UUID, list] = {}
        for ph in all_prices:
            prices_by_product.setdefault(ph.normalized_product_id, []).append(ph)

        products = []
        for pid in filtered_product_ids:
            product = products_by_id.get(pid)
            if not product:
                continue
            products.append(
                {
                    "product_id": pid,
                    "product_name": product.canonical_name,
                    "prices": [
                        {
                            "store_id": ph.store_id,
                            "store_name": ph.store.name,
                            "current_price": float(ph.regular_price),
                            "last_seen_at": ph.observed_date,
                        }
                        for ph in prices_by_product.get(pid, [])
                    ],
                }
            )

        return {"products": products}

    async def get_inflation(self, category: str | None = None, period: str = "all-time") -> dict:
        """Aggregate price change stats. Compares average prices across periods."""
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        date_threshold = None
        if period != "all-time":
            days_map = {"1y": 365, "6m": 180, "3m": 90, "1m": 30}
            days = days_map.get(period, 365)
            date_threshold = date.today() - timedelta(days=days)

        query = select(
            NormalizedProduct.category,
            func.avg(PriceHistory.regular_price),
        ).join(NormalizedProduct)

        if category:
            query = query.where(NormalizedProduct.category == category)
        if date_threshold:
            query = query.where(PriceHistory.observed_date >= date_threshold)

        query = query.group_by(NormalizedProduct.category)

        result = await self.db.execute(query)
        categories = {}
        for row in result.all():
            cat, avg_price = row
            if cat:
                categories[cat] = float(avg_price) if avg_price else 0.0

        return {
            "period": period,
            "cartsnitch_index": sum(categories.values()) / max(len(categories), 1),
            "cpi_baseline": 100.0,
            "categories": categories,
        }
