"""Integration tests for coupon endpoints."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cartsnitch_api.models import Coupon, Store


@pytest.fixture
async def coupon_data(db_engine, auth_headers):
    """Seed stores and coupons."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = Store(name="Target", slug="target")
        session.add(store)
        await session.commit()
        await session.refresh(store)

        coupon = Coupon(
            store_id=store.id,
            title="$2 off laundry",
            description="$2 off any laundry detergent",
            discount_value=Decimal("2.00"),
            discount_type="fixed",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 12, 31),
        )
        session.add(coupon)
        await session.commit()

        return {"store": store, "coupon": coupon, "headers": auth_headers}


@pytest.mark.asyncio
async def test_list_coupons(client, coupon_data):
    resp = await client.get("/coupons", headers=coupon_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_coupons_by_store(client, coupon_data):
    store_id = str(coupon_data["store"].id)
    resp = await client.get(f"/coupons?store_id={store_id}", headers=coupon_data["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_relevant_coupons_empty(client, auth_headers):
    """No purchases means no relevant coupons."""
    resp = await client.get("/coupons/relevant", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
