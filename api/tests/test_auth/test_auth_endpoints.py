"""Integration tests for auth endpoints."""

import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "password": "securepass123",
            "display_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900  # 15 min * 60


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/auth/register",
        json={
            "email": "dupe@example.com",
            "password": "securepass123",
            "display_name": "User One",
        },
    )
    resp = await client.post(
        "/auth/register",
        json={
            "email": "dupe@example.com",
            "password": "securepass456",
            "display_name": "User Two",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "display_name": "Short Pass",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "securepass123",
            "display_name": "Login User",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "securepass123",
            "display_name": "Wrong Pass",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "badpassword1",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    resp = await client.post(
        "/auth/login",
        json={
            "email": "ghost@example.com",
            "password": "doesntmatter",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    reg = await client.post(
        "/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "securepass123",
            "display_name": "Refresh User",
        },
    )
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client):
    resp = await client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid.token.here",
        },
    )
    assert resp.status_code == 401


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
    assert resp.status_code in (401, 403)  # No auth header


@pytest.mark.asyncio
async def test_update_me(client, auth_headers):
    resp = await client.patch(
        "/auth/me",
        headers=auth_headers,
        json={
            "display_name": "Updated Name",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_me(client, auth_headers):
    resp = await client.delete("/auth/me", headers=auth_headers)
    assert resp.status_code == 204

    # Verify user is gone (token still valid but user deleted)
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refresh_after_delete_fails(client):
    """Refresh token for a deleted user must be rejected."""
    reg = await client.post(
        "/auth/register",
        json={
            "email": "ghost@example.com",
            "password": "securepass123",
            "display_name": "Ghost User",
        },
    )
    tokens = reg.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Delete the user
    resp = await client.delete("/auth/me", headers=headers)
    assert resp.status_code == 204

    # Refresh token should now fail
    resp = await client.post(
        "/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )
    assert resp.status_code == 401
