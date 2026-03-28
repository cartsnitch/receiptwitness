"""E2E: Error responses for bad input across all endpoint categories."""

import pytest

from tests.test_e2e.conftest import BAD_UUID, ZERO_UUID


@pytest.mark.asyncio
class TestRegistrationErrors:
    """Validation errors during user registration."""

    async def test_short_password(self, client, db_engine):
        resp = await client.post(
            "/auth/register",
            json={"email": "short@example.com", "password": "short", "display_name": "Test"},
        )
        assert resp.status_code == 422

    async def test_invalid_email(self, client, db_engine):
        resp = await client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "securepass123", "display_name": "Test"},
        )
        assert resp.status_code == 422

    async def test_missing_fields(self, client, db_engine):
        resp = await client.post("/auth/register", json={})
        assert resp.status_code == 422

    async def test_empty_display_name(self, client, db_engine):
        resp = await client.post(
            "/auth/register",
            json={"email": "empty@example.com", "password": "securepass123", "display_name": ""},
        )
        assert resp.status_code == 422

    async def test_duplicate_email(self, client, db_engine):
        payload = {
            "email": "dupe@example.com",
            "password": "securepass123",
            "display_name": "First",
        }
        first = await client.post("/auth/register", json=payload)
        assert first.status_code == 201
        second = await client.post("/auth/register", json=payload)
        assert second.status_code == 409


@pytest.mark.asyncio
class TestLoginErrors:
    """Login failure modes."""

    async def test_wrong_password(self, client, db_engine):
        await client.post(
            "/auth/register",
            json={
                "email": "login-err@example.com",
                "password": "correctpass1",
                "display_name": "Login",
            },
        )
        resp = await client.post(
            "/auth/login",
            json={"email": "login-err@example.com", "password": "wrongpass123"},
        )
        assert resp.status_code == 401

    async def test_nonexistent_user(self, client, db_engine):
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "doesntmatter"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestNotFoundErrors:
    """404 responses for missing resources."""

    async def test_product_not_found(self, client, seed_data):
        resp = await client.get(f"/products/{ZERO_UUID}", headers=seed_data["headers"])
        assert resp.status_code == 404

    async def test_purchase_not_found(self, client, seed_data):
        resp = await client.get(f"/purchases/{ZERO_UUID}", headers=seed_data["headers"])
        assert resp.status_code == 404

    async def test_public_trend_not_found(self, client, seed_data):
        resp = await client.get(f"/public/trends/{ZERO_UUID}")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestMalformedInput:
    """Invalid UUID formats and bad query params."""

    async def test_invalid_uuid_product(self, client, seed_data):
        resp = await client.get(f"/products/{BAD_UUID}", headers=seed_data["headers"])
        assert resp.status_code == 422

    async def test_invalid_uuid_purchase(self, client, seed_data):
        resp = await client.get(f"/purchases/{BAD_UUID}", headers=seed_data["headers"])
        assert resp.status_code == 422

    async def test_invalid_uuid_public_trend(self, client, seed_data):
        resp = await client.get(f"/public/trends/{BAD_UUID}")
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestStoreConnectionErrors:
    """Store connection edge cases."""

    async def test_connect_nonexistent_store(self, client, seed_data):
        resp = await client.post(
            "/me/stores/nonexistent-store/connect",
            json={},
            headers=seed_data["headers"],
        )
        assert resp.status_code == 404

    async def test_connect_store_twice(self, client, seed_data):
        headers = seed_data["headers"]
        first = await client.post("/me/stores/meijer/connect", json={}, headers=headers)
        assert first.status_code in (200, 201)
        second = await client.post("/me/stores/meijer/connect", json={}, headers=headers)
        assert second.status_code == 409
