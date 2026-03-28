"""E2E: Auth and session validation flows.

Registration and login are handled by the Better-Auth service.
These tests validate session token handling at the API gateway level.
"""

import pytest

from tests.conftest import _create_test_user_and_session


@pytest.mark.asyncio
class TestSessionValidation:
    """Session edge cases and error responses."""

    async def test_invalid_session_token_rejected(self, client, db_engine):
        resp = await client.get(
            "/auth/me",
            headers={"Cookie": "better-auth.session_token=not-a-real-token"},
        )
        assert resp.status_code == 401

    async def test_missing_auth(self, client, db_engine):
        resp = await client.get("/auth/me")
        assert resp.status_code in (401, 403)

    async def test_bearer_token_also_works(self, client, db_engine):
        """Session tokens passed as Bearer tokens should also be accepted."""
        _, session_token = await _create_test_user_and_session(
            client, db_engine, email="bearer@e2e.com", display_name="Bearer E2E"
        )
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {session_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "bearer@e2e.com"

    async def test_deleted_user_session_returns_not_found(self, client, db_engine):
        """After deleting a user, their session should result in 404 for profile."""
        _, session_token = await _create_test_user_and_session(
            client, db_engine, email="delete-me@e2e.com", display_name="Delete Me"
        )
        headers = {"Cookie": f"better-auth.session_token={session_token}"}

        delete_resp = await client.delete("/auth/me", headers=headers)
        assert delete_resp.status_code == 204

        me = await client.get("/auth/me", headers=headers)
        assert me.status_code == 404

    async def test_expired_session_rejected(self, client, db_engine):
        """Expired sessions must be rejected."""
        import secrets
        import uuid
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import text

        user_id = str(uuid.uuid4())
        session_token = secrets.token_urlsafe(32)
        now = datetime.now(UTC).isoformat()
        expired = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

        async with db_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, display_name, email_verified, created_at, updated_at) "
                    "VALUES (:id, :email, :hp, :dn, :ev, :ca, :ua)"
                ),
                {
                    "id": user_id,
                    "email": "expired@e2e.com",
                    "hp": "unused",
                    "dn": "Expired User",
                    "ev": False,
                    "ca": now,
                    "ua": now,
                },
            )
            await conn.execute(
                text(
                    "INSERT INTO sessions (id, token, user_id, expires_at, created_at, updated_at) "
                    "VALUES (:id, :token, :uid, :ea, :ca, :ua)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "token": session_token,
                    "uid": user_id,
                    "ea": expired,
                    "ca": now,
                    "ua": now,
                },
            )

        resp = await client.get(
            "/auth/me",
            headers={"Cookie": f"better-auth.session_token={session_token}"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestAuthProtectedEndpoints:
    """Verify auth is enforced on all user-specific endpoints."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/purchases"),
            ("GET", "/products"),
            ("GET", "/prices/trends"),
            ("GET", "/prices/increases"),
            ("GET", "/coupons"),
            ("GET", "/alerts"),
            ("GET", "/me/stores"),
        ],
    )
    async def test_endpoints_require_auth(self, client, db_engine, method, path):
        resp = await client.request(method, path)
        assert resp.status_code in (401, 403), f"{method} {path} should require auth"


@pytest.mark.asyncio
class TestCrossUserDataIsolation:
    """Verify that users cannot access other users' data."""

    async def test_user_b_cannot_access_user_a_purchases(self, client, db_engine, seed_data):
        """A second user cannot see User A's purchases."""
        purchase_id = str(seed_data["purchases"]["meijer_trip"].id)

        _, session_token = await _create_test_user_and_session(
            client, db_engine, email="userb@e2e.com", display_name="User B"
        )
        user_b_headers = {"Cookie": f"better-auth.session_token={session_token}"}

        resp = await client.get(f"/purchases/{purchase_id}", headers=user_b_headers)
        assert resp.status_code in (403, 404), (
            "User B should not be able to access User A's purchase"
        )

    async def test_user_b_purchase_list_is_empty(self, client, db_engine, seed_data):
        """A new user should see no purchases."""
        _, session_token = await _create_test_user_and_session(
            client, db_engine, email="userc@e2e.com", display_name="User C"
        )
        user_c_headers = {"Cookie": f"better-auth.session_token={session_token}"}

        resp = await client.get("/purchases", headers=user_c_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0, "New user should have no purchases"

    async def test_user_b_stores_isolated(self, client, db_engine, seed_data):
        """User B's connected stores should be independent from User A."""
        _, session_token = await _create_test_user_and_session(
            client, db_engine, email="userd@e2e.com", display_name="User D"
        )
        user_d_headers = {"Cookie": f"better-auth.session_token={session_token}"}

        resp = await client.get("/me/stores", headers=user_d_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0, "New user should have no connected stores"
