"""Integration tests for product endpoints."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.models import NormalizedProduct, PriceHistory, Store


@pytest.fixture
async def product_data(db_engine, auth_headers):
    """Seed products and price history."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = Store(name="Meijer", slug="meijer")
        product = NormalizedProduct(
            canonical_name="Cheerios 18oz",
            category="pantry",
            brand="General Mills",
            upc_variants=["016000275263"],
        )
        session.add_all([store, product])
        await session.commit()
        await session.refresh(store)
        await session.refresh(product)

        ph1 = PriceHistory(
            normalized_product_id=product.id,
            store_id=store.id,
            observed_date=date(2026, 3, 1),
            regular_price=Decimal("4.99"),
            source="receipt",
        )
        ph2 = PriceHistory(
            normalized_product_id=product.id,
            store_id=store.id,
            observed_date=date(2026, 3, 10),
            regular_price=Decimal("5.49"),
            source="receipt",
        )
        session.add_all([ph1, ph2])
        await session.commit()

        return {"product": product, "store": store, "headers": auth_headers}


@pytest.mark.asyncio
async def test_list_products(client, product_data):
    resp = await client.get("/products", headers=product_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Cheerios 18oz"


@pytest.mark.asyncio
async def test_search_products(client, product_data):
    resp = await client.get("/products?q=Cheerios", headers=product_data["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/products?q=nonexistent", headers=product_data["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_get_product_detail(client, product_data):
    pid = str(product_data["product"].id)
    resp = await client.get(f"/products/{pid}", headers=product_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Cheerios 18oz"
    assert data["brand"] == "General Mills"
    assert len(data["prices_by_store"]) >= 1


@pytest.mark.asyncio
async def test_get_product_not_found(client, auth_headers):
    resp = await client.get(f"/products/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_product_prices(client, product_data):
    pid = str(product_data["product"].id)
    resp = await client.get(f"/products/{pid}/prices", headers=product_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_name"] == "Cheerios 18oz"
    assert len(data["data_points"]) == 2
