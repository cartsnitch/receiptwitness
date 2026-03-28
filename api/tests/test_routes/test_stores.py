"""Integration tests for store endpoints."""

import pytest

from cartsnitch_api.models import Store


@pytest.fixture
async def seeded_store(db_engine):
    """Insert a test store directly into the DB."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = Store(name="Meijer", slug="meijer", logo_url=None, website_url=None)
        session.add(store)
        await session.commit()
        await session.refresh(store)
        return store


@pytest.mark.asyncio
async def test_list_stores(client, seeded_store):
    resp = await client.get("/stores")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["slug"] == "meijer"


@pytest.mark.asyncio
async def test_list_user_stores_empty(client, auth_headers):
    resp = await client.get("/me/stores", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_connect_and_disconnect_store(client, auth_headers, seeded_store):
    # Connect
    resp = await client.post(
        "/me/stores/meijer/connect",
        headers=auth_headers,
        json={"credentials": None},
    )
    assert resp.status_code == 201
    assert resp.json()["connected"] is True

    # List should show connected
    resp = await client.get("/me/stores", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Disconnect
    resp = await client.delete("/me/stores/meijer", headers=auth_headers)
    assert resp.status_code == 204

    # List should be empty again
    resp = await client.get("/me/stores", headers=auth_headers)
    assert resp.json() == []


@pytest.mark.asyncio
async def test_connect_nonexistent_store(client, auth_headers):
    resp = await client.post(
        "/me/stores/nonexistent/connect",
        headers=auth_headers,
        json={},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_connect_duplicate_store(client, auth_headers, seeded_store):
    await client.post("/me/stores/meijer/connect", headers=auth_headers, json={})
    resp = await client.post("/me/stores/meijer/connect", headers=auth_headers, json={})
    assert resp.status_code == 409
