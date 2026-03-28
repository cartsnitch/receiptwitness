"""Product service — catalog, detail, price history."""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cartsnitch_api.services.queries import latest_price_per_store


class ProductService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_products(
        self,
        q: str | None = None,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        from cartsnitch_api.models import NormalizedProduct

        query = select(NormalizedProduct)
        if q:
            # Escape SQL LIKE wildcards in user input
            safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.where(NormalizedProduct.canonical_name.ilike(f"%{safe_q}%"))
        if category:
            query = query.where(NormalizedProduct.category == category)
        query = query.order_by(NormalizedProduct.canonical_name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        products = result.scalars().all()
        return [
            {
                "id": p.id,
                "name": p.canonical_name,
                "brand": p.brand,
                "category": p.category,
                "upc": (p.upc_variants[0] if p.upc_variants else None),
                "image_url": None,
            }
            for p in products
        ]

    async def get_product(self, product_id: UUID) -> dict:
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        result = await self.db.execute(
            select(NormalizedProduct).where(NormalizedProduct.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise LookupError("Product not found")

        # Get latest price per store
        subq = latest_price_per_store([product_id])
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
            .where(PriceHistory.normalized_product_id == product_id)
            .options(selectinload(PriceHistory.store))
        )
        prices = prices_result.scalars().all()

        return {
            "id": product.id,
            "name": product.canonical_name,
            "brand": product.brand,
            "category": product.category,
            "upc": (product.upc_variants[0] if product.upc_variants else None),
            "image_url": None,
            "prices_by_store": [
                {
                    "store_id": ph.store_id,
                    "store_name": ph.store.name,
                    "current_price": float(ph.regular_price),
                    "last_seen_at": ph.observed_date,
                }
                for ph in prices
            ],
        }

    async def get_price_history(self, product_id: UUID) -> dict:
        from cartsnitch_api.models import NormalizedProduct, PriceHistory

        result = await self.db.execute(
            select(NormalizedProduct).where(NormalizedProduct.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise LookupError("Product not found")

        prices_result = await self.db.execute(
            select(PriceHistory)
            .where(PriceHistory.normalized_product_id == product_id)
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
