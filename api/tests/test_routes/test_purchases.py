"""Integration tests for purchase endpoints."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.auth.jwt import create_access_token
from cartsnitch_api.models import Purchase, PurchaseItem, Store, User


@pytest.fixture
async def purchase_data(db_engine):
    """Seed a user, store, purchase, and items."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        from cartsnitch_api.auth.passwords import hash_password

        user = User(
            email="buyer@example.com",
            hashed_password=hash_password("testpass123"),
            display_name="Buyer",
        )
        store = Store(name="Kroger", slug="kroger")
        session.add_all([user, store])
        await session.commit()
        await session.refresh(user)
        await session.refresh(store)

        purchase = Purchase(
            user_id=user.id,
            store_id=store.id,
            receipt_id="receipt-001",
            purchase_date=date(2026, 3, 10),
            total=Decimal("42.50"),
        )
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)

        item = PurchaseItem(
            purchase_id=purchase.id,
            product_name_raw="Organic Milk 1gal",
            quantity=Decimal("1"),
            unit_price=Decimal("5.99"),
            extended_price=Decimal("5.99"),
        )
        session.add(item)
        await session.commit()

        token = create_access_token(user.id)
        return {
            "user": user,
            "store": store,
            "purchase": purchase,
            "headers": {"Authorization": f"Bearer {token}"},
        }


@pytest.mark.asyncio
async def test_list_purchases(client, purchase_data):
    resp = await client.get("/purchases", headers=purchase_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["store_name"] == "Kroger"
    assert data[0]["total"] == 42.50


@pytest.mark.asyncio
async def test_get_purchase_detail(client, purchase_data):
    pid = str(purchase_data["purchase"].id)
    resp = await client.get(f"/purchases/{pid}", headers=purchase_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["line_items"]) == 1
    assert data["line_items"][0]["name"] == "Organic Milk 1gal"


@pytest.mark.asyncio
async def test_get_purchase_not_found(client, auth_headers):
    resp = await client.get(f"/purchases/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_purchase_stats(client, purchase_data):
    resp = await client.get("/purchases/stats", headers=purchase_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_spent"] == 42.50
    assert data["purchase_count"] == 1
    assert "Kroger" in data["by_store"]
