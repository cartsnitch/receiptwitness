"""Integration tests for purchase endpoints."""

import secrets
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.models import Purchase, PurchaseItem, Store, User


@pytest.fixture
async def purchase_data(db_engine):
    """Seed a user, store, purchase, items, and a valid session."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        user = User(
            email="buyer@example.com",
            hashed_password="not-used-with-better-auth",
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

    # Create a session token directly in the sessions table
    session_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC).isoformat()
    expires = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO sessions (id, token, user_id, expires_at, created_at, updated_at) "
                "VALUES (:id, :token, :user_id, :expires_at, :created_at, :updated_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "token": session_token,
                "user_id": str(user.id),
                "expires_at": expires,
                "created_at": now,
                "updated_at": now,
            },
        )

    return {
        "user": user,
        "store": store,
        "purchase": purchase,
        "headers": {"Cookie": f"better-auth.session_token={session_token}"},
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
