"""Integration tests for price endpoints."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.models import NormalizedProduct, PriceHistory, Store


@pytest.fixture
async def price_data(db_engine, auth_headers):
    """Seed products with price history showing an increase."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = Store(name="Walmart", slug="walmart")
        product = NormalizedProduct(
            canonical_name="Tide Pods 42ct",
            category="household",
            brand="Tide",
        )
        session.add_all([store, product])
        await session.commit()
        await session.refresh(store)
        await session.refresh(product)

        # Two price points — second is higher (increase)
        ph1 = PriceHistory(
            normalized_product_id=product.id,
            store_id=store.id,
            observed_date=date(2026, 2, 1),
            regular_price=Decimal("12.99"),
            source="receipt",
        )
        ph2 = PriceHistory(
            normalized_product_id=product.id,
            store_id=store.id,
            observed_date=date(2026, 3, 1),
            regular_price=Decimal("14.49"),
            source="receipt",
        )
        session.add_all([ph1, ph2])
        await session.commit()

        return {"product": product, "store": store, "headers": auth_headers}


@pytest.mark.asyncio
async def test_price_trends(client, price_data):
    resp = await client.get("/prices/trends", headers=price_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["product_name"] == "Tide Pods 42ct"
    assert len(data[0]["data_points"]) == 2


@pytest.mark.asyncio
async def test_price_trends_by_category(client, price_data):
    resp = await client.get("/prices/trends?category=household", headers=price_data["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/prices/trends?category=nonexistent", headers=price_data["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_price_increases(client, price_data):
    resp = await client.get("/prices/increases", headers=price_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    increase = data[0]
    assert increase["old_price"] == 12.99
    assert increase["new_price"] == 14.49
    assert increase["increase_pct"] > 0


@pytest.mark.asyncio
async def test_price_comparison(client, price_data):
    pid = str(price_data["product"].id)
    resp = await client.get(f"/prices/comparison?product_ids={pid}", headers=price_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["product_name"] == "Tide Pods 42ct"
    assert len(data[0]["prices"]) >= 1
