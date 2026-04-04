"""Integration tests for auth profile endpoints.

Registration, login, and session management are handled by the Better-Auth
service. These tests cover the profile endpoints (GET/PATCH/DELETE /auth/me)
which validate sessions via the shared sessions table.
"""

import pytest


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    resp = await client.get("/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_invalid_session(client):
    resp = await client.get(
        "/auth/me",
        headers={"Cookie": "better-auth.session_token=invalid-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_bearer_token(client, db_engine):
    """Session tokens can also be passed as Bearer tokens for API clients."""
    from tests.conftest import _create_test_user_and_session

    _, session_token = await _create_test_user_and_session(
        client, db_engine, email="bearer@example.com", display_name="Bearer User"
    )
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {session_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "bearer@example.com"


@pytest.mark.asyncio
async def test_update_me(client, auth_headers):
    resp = await client.patch(
        "/auth/me",
        headers=auth_headers,
        json={"display_name": "Updated Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_me(client, auth_headers):
    resp = await client.delete("/auth/me", headers=auth_headers)
    assert resp.status_code == 204

    # Session is still valid but user is gone
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_expired_session_rejected(client, db_engine):
    """Expired sessions must be rejected."""
    import hashlib
    import secrets
    import uuid
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    user_id = str(uuid.uuid4())
    session_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(session_token.encode()).hexdigest()
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
                "email": "expired@example.com",
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
                "token": token_hash,
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
