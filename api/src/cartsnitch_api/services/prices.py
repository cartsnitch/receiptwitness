"""Price service — trends, increases, comparison."""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cartsnitch_api.services.queries import latest_price_per_store


class PriceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_trends(self, category: str | None = None) -> list[dict]:
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        query = (
            select(PriceHistory)
            .join(NormalizedProduct)
            .options(
                selectinload(PriceHistory.store),
                selectinload(PriceHistory.normalized_product),
            )
            .order_by(PriceHistory.observed_date)
        )
        if category:
            query = query.where(NormalizedProduct.category == category)

        result = await self.db.execute(query)
        prices = result.scalars().all()

        # Group by product
        by_product: dict[UUID, dict] = {}
        for ph in prices:
            pid = ph.normalized_product_id
            if pid not in by_product:
                by_product[pid] = {
                    "product_id": pid,
                    "product_name": ph.normalized_product.canonical_name,
                    "data_points": [],
                }
            by_product[pid]["data_points"].append(
                {
                    "date": ph.observed_date,
                    "price": float(ph.regular_price),
                    "store_id": ph.store_id,
                    "store_name": ph.store.name,
                }
            )
        return list(by_product.values())

    async def get_increases(self) -> list[dict]:
        """Find products with recent significant price increases.

        Uses a window function (lag) to compare each price observation with the
        previous one per product+store, avoiding the N+1 query pattern.
        """
        from cartsnitch_api.models import NormalizedProduct, PriceHistory, Store

        # Use lag() window function to get previous price in a single query
        prev_price = (
            func.lag(PriceHistory.regular_price)
            .over(
                partition_by=[PriceHistory.normalized_product_id, PriceHistory.store_id],
                order_by=PriceHistory.observed_date,
            )
            .label("prev_price")
        )

        row_num = (
            func.row_number()
            .over(
                partition_by=[PriceHistory.normalized_product_id, PriceHistory.store_id],
                order_by=PriceHistory.observed_date.desc(),
            )
            .label("rn")
        )

        inner = select(
            PriceHistory.normalized_product_id,
            PriceHistory.store_id,
            PriceHistory.regular_price,
            PriceHistory.observed_date,
            prev_price,
            row_num,
        ).subquery()

        # Only keep the latest row (rn=1) where price increased
        result = await self.db.execute(
            select(
                inner.c.normalized_product_id,
                inner.c.store_id,
                inner.c.regular_price,
                inner.c.observed_date,
                inner.c.prev_price,
                NormalizedProduct.canonical_name,
                Store.name.label("store_name"),
            )
            .join(NormalizedProduct, NormalizedProduct.id == inner.c.normalized_product_id)
            .join(Store, Store.id == inner.c.store_id)
            .where(
                inner.c.rn == 1,
                inner.c.prev_price.isnot(None),
                inner.c.regular_price > inner.c.prev_price,
            )
        )

        increases = []
        for row in result.all():
            old = float(row.prev_price)
            new = float(row.regular_price)
            increases.append(
                {
                    "product_id": row.normalized_product_id,
                    "product_name": row.canonical_name,
                    "store_name": row.store_name,
                    "old_price": old,
                    "new_price": new,
                    "increase_pct": round((new - old) / old * 100, 2),
                    "detected_at": row.observed_date,
                }
            )

        increases.sort(key=lambda x: x["increase_pct"], reverse=True)
        return increases

    async def get_comparison(self, product_ids: list[UUID]) -> list[dict]:
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        if not product_ids:
            return []

        # Fetch all requested products in one query
        prod_result = await self.db.execute(
            select(NormalizedProduct).where(NormalizedProduct.id.in_(product_ids))
        )
        products_by_id = {p.id: p for p in prod_result.scalars().all()}

        # Latest prices for all requested products in one query
        subq = latest_price_per_store(product_ids)
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
            .where(PriceHistory.normalized_product_id.in_(product_ids))
            .options(selectinload(PriceHistory.store))
        )
        all_prices = prices_result.scalars().all()

        # Group prices by product
        prices_by_product: dict[UUID, list] = {pid: [] for pid in product_ids}
        for ph in all_prices:
            prices_by_product.setdefault(ph.normalized_product_id, []).append(ph)

        comparisons = []
        for pid in product_ids:
            product = products_by_id.get(pid)
            if not product:
                continue
            comparisons.append(
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
        return comparisons
