"""Integration tests for public endpoints (no auth)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.models import NormalizedProduct, PriceHistory, Store


@pytest.fixture
async def public_data(db_engine):
    """Seed data for public endpoints."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = Store(name="Target", slug="target")
        product = NormalizedProduct(
            canonical_name="Skippy PB 16oz",
            category="pantry",
            brand="Skippy",
        )
        session.add_all([store, product])
        await session.commit()
        await session.refresh(store)
        await session.refresh(product)

        ph = PriceHistory(
            normalized_product_id=product.id,
            store_id=store.id,
            observed_date=date(2026, 3, 5),
            regular_price=Decimal("3.99"),
            source="receipt",
        )
        session.add(ph)
        await session.commit()

        return {"product": product, "store": store}


@pytest.mark.asyncio
async def test_public_trend(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/trends/{pid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_name"] == "Skippy PB 16oz"
    assert len(data["data_points"]) == 1


@pytest.mark.asyncio
async def test_public_trend_not_found(client):
    resp = await client.get(f"/public/trends/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_store_comparison(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/store-comparison?product_ids={pid}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) == 1


@pytest.mark.asyncio
async def test_public_inflation(client, public_data):
    resp = await client.get("/public/inflation")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert "cartsnitch_index" in data
