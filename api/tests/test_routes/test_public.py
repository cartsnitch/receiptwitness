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


@pytest.mark.asyncio
async def test_trend_invalid_uuid(client):
    resp = await client.get("/public/trends/not-a-uuid")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_trend_days_zero(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/trends/{pid}?days=0")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_trend_days_negative(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/trends/{pid}?days=-1")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_trend_days_over_max(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/trends/{pid}?days=999")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_trend_days_valid(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/trends/{pid}?days=30")
    assert resp.status_code == 200
    assert "product_name" in resp.json()


@pytest.mark.asyncio
async def test_store_comparison_empty_list(client):
    resp = await client.get("/public/store-comparison")
    assert resp.status_code == 400
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_store_comparison_category_xss(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(
        f"/public/store-comparison?product_ids={pid}&category=<script>alert(1)</script>"
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_store_comparison_category_sql_injection(client, public_data):
    pid = str(public_data["product"].id)
    resp = await client.get(f"/public/store-comparison?product_ids={pid}&category='; DROP TABLE--")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_inflation_invalid_period(client, public_data):
    resp = await client.get("/public/inflation?period=10years")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()


@pytest.mark.asyncio
async def test_inflation_valid_periods(client, public_data):
    for period in ["all-time", "1y", "6m", "3m", "1m"]:
        resp = await client.get(f"/public/inflation?period={period}")
        assert resp.status_code == 200, f"period={period} failed"


@pytest.mark.asyncio
async def test_inflation_category_too_long(client, public_data):
    long_category = "x" * 200
    resp = await client.get(f"/public/inflation?category={long_category}")
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert "stack" not in resp.json()
