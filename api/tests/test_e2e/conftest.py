"""Shared fixtures for E2E integration tests.

Seeds a realistic dataset with stores, products, price history,
purchases, coupons, and shrinkflation events so E2E flows can
exercise cross-resource queries against real data.
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.models import (
    Coupon,
    NormalizedProduct,
    PriceHistory,
    Purchase,
    PurchaseItem,
    ShrinkflationEvent,
    Store,
)

# Shared test constants
ZERO_UUID = "00000000-0000-0000-0000-000000000000"
BAD_UUID = "not-a-uuid"
# Fixed anchor date for deterministic tests
ANCHOR_DATE = date(2026, 3, 15)


@pytest.fixture
async def seed_data(db_engine, auth_headers):
    """Seed a full dataset and return identifiers for test assertions."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        # -- Stores --
        meijer = Store(name="Meijer", slug="meijer")
        kroger = Store(name="Kroger", slug="kroger")
        target = Store(name="Target", slug="target")
        session.add_all([meijer, kroger, target])
        await session.flush()

        # -- Products --
        cheerios = NormalizedProduct(
            canonical_name="Cheerios 18oz",
            category="pantry",
            brand="General Mills",
            size="18",
            size_unit="oz",
            upc_variants=["016000275263"],
        )
        milk = NormalizedProduct(
            canonical_name="Whole Milk 1gal",
            category="dairy",
            brand="Meijer",
            size="1",
            size_unit="gal",
        )
        chicken = NormalizedProduct(
            canonical_name="Chicken Breast 1lb",
            category="meat",
            brand=None,
            size="1",
            size_unit="lb",
        )
        session.add_all([cheerios, milk, chicken])
        await session.flush()

        # -- Price history (multiple dates, multiple stores) --
        today = ANCHOR_DATE
        prices = []
        # Cheerios at Meijer: price increase over time
        for i, price_val in enumerate([Decimal("3.99"), Decimal("4.29"), Decimal("4.79")]):
            prices.append(
                PriceHistory(
                    normalized_product_id=cheerios.id,
                    store_id=meijer.id,
                    observed_date=today - timedelta(days=60 - i * 30),
                    regular_price=price_val,
                    source="receipt",
                )
            )
        # Cheerios at Kroger: stable price
        for i in range(3):
            prices.append(
                PriceHistory(
                    normalized_product_id=cheerios.id,
                    store_id=kroger.id,
                    observed_date=today - timedelta(days=60 - i * 30),
                    regular_price=Decimal("4.49"),
                    source="catalog",
                )
            )
        # Milk at Meijer
        prices.append(
            PriceHistory(
                normalized_product_id=milk.id,
                store_id=meijer.id,
                observed_date=today - timedelta(days=7),
                regular_price=Decimal("3.29"),
                source="receipt",
            )
        )
        # Milk at Kroger
        prices.append(
            PriceHistory(
                normalized_product_id=milk.id,
                store_id=kroger.id,
                observed_date=today - timedelta(days=5),
                regular_price=Decimal("3.49"),
                source="catalog",
            )
        )
        # Chicken at Target
        prices.append(
            PriceHistory(
                normalized_product_id=chicken.id,
                store_id=target.id,
                observed_date=today - timedelta(days=3),
                regular_price=Decimal("5.99"),
                source="catalog",
            )
        )
        session.add_all(prices)
        await session.flush()

        # -- Get the user_id from the session token in auth_headers --
        cookie_str = auth_headers.get("Cookie", "")
        session_token = cookie_str.split("=", 1)[1] if "=" in cookie_str else ""

        result = await session.execute(
            text("SELECT user_id FROM sessions WHERE token = :token"),
            {"token": session_token},
        )
        row = result.first()
        user_id = UUID(row[0])

        purchase1 = Purchase(
            user_id=user_id,
            store_id=meijer.id,
            receipt_id="meijer-2026-001",
            purchase_date=today - timedelta(days=10),
            total=Decimal("23.45"),
            subtotal=Decimal("21.50"),
            tax=Decimal("1.95"),
        )
        purchase2 = Purchase(
            user_id=user_id,
            store_id=kroger.id,
            receipt_id="kroger-2026-001",
            purchase_date=today - timedelta(days=5),
            total=Decimal("15.78"),
            subtotal=Decimal("14.50"),
            tax=Decimal("1.28"),
        )
        session.add_all([purchase1, purchase2])
        await session.flush()

        # -- Purchase Items --
        item1 = PurchaseItem(
            purchase_id=purchase1.id,
            product_name_raw="Cheerios 18oz Box",
            quantity=Decimal("1"),
            unit_price=Decimal("4.79"),
            extended_price=Decimal("4.79"),
            normalized_product_id=cheerios.id,
        )
        item2 = PurchaseItem(
            purchase_id=purchase1.id,
            product_name_raw="Meijer Whole Milk 1gal",
            quantity=Decimal("2"),
            unit_price=Decimal("3.29"),
            extended_price=Decimal("6.58"),
            normalized_product_id=milk.id,
        )
        item3 = PurchaseItem(
            purchase_id=purchase2.id,
            product_name_raw="KRO CHEERIOS 18OZ",
            quantity=Decimal("1"),
            unit_price=Decimal("4.49"),
            extended_price=Decimal("4.49"),
            normalized_product_id=cheerios.id,
        )
        session.add_all([item1, item2, item3])
        await session.flush()

        # -- Coupons --
        coupon1 = Coupon(
            store_id=meijer.id,
            normalized_product_id=cheerios.id,
            title="$1 off Cheerios",
            description="Save $1 on any Cheerios 18oz or larger",
            discount_type="fixed",
            discount_value=Decimal("1.00"),
            valid_from=today - timedelta(days=7),
            valid_to=today + timedelta(days=30),
        )
        coupon2 = Coupon(
            store_id=kroger.id,
            normalized_product_id=None,
            title="10% off dairy",
            description="10% off all dairy products",
            discount_type="percent",
            discount_value=Decimal("10.00"),
            valid_from=today - timedelta(days=3),
            valid_to=today + timedelta(days=14),
        )
        session.add_all([coupon1, coupon2])
        await session.flush()

        # -- Shrinkflation events --
        shrink = ShrinkflationEvent(
            normalized_product_id=cheerios.id,
            detected_date=today - timedelta(days=15),
            old_size="20",
            new_size="18",
            old_unit="oz",
            new_unit="oz",
            price_at_old_size=Decimal("3.99"),
            price_at_new_size=Decimal("4.29"),
            confidence=Decimal("0.95"),
            notes="Size reduced from 20oz to 18oz while price increased",
        )
        session.add(shrink)
        await session.commit()

        for obj in [
            meijer,
            kroger,
            target,
            cheerios,
            milk,
            chicken,
            purchase1,
            purchase2,
            item1,
            item2,
            item3,
            coupon1,
            coupon2,
            shrink,
        ]:
            await session.refresh(obj)

        return {
            "headers": auth_headers,
            "user_id": user_id,
            "stores": {"meijer": meijer, "kroger": kroger, "target": target},
            "products": {"cheerios": cheerios, "milk": milk, "chicken": chicken},
            "purchases": {"meijer_trip": purchase1, "kroger_trip": purchase2},
            "items": {"cheerios_meijer": item1, "milk_meijer": item2, "cheerios_kroger": item3},
            "coupons": {"cheerios_coupon": coupon1, "dairy_coupon": coupon2},
            "shrinkflation": {"cheerios_shrink": shrink},
        }
