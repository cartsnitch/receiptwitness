"""Tests for GET /api/v1/me/email-in-address endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_email_in_address_authenticated(client: AsyncClient, auth_headers: dict):
    """Authenticated user gets their email-in address."""
    response = await client.get(
        "/api/v1/me/email-in-address",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "email_address" in data
    assert data["email_address"].startswith("receipts+")
    assert data["email_address"].endswith("@receipts.cartsnitch.com")
    assert len(data["email_address"]) > len("receipts+@receipts.cartsnitch.com")
    assert "instructions" in data
    assert "Meijer" in data["instructions"]
    assert "Kroger" in data["instructions"]
    assert "Target" in data["instructions"]


@pytest.mark.asyncio
async def test_get_email_in_address_unauthenticated(client: AsyncClient):
    """Unauthenticated request returns 401."""
    response = await client.get("/api/v1/me/email-in-address")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_email_in_address_invalid_token(client: AsyncClient):
    """Invalid JWT token returns 401."""
    response = await client.get(
        "/api/v1/me/email-in-address",
        headers={"Authorization": "Bearer invalid-token-xyz"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_email_address_format(client: AsyncClient, auth_headers: dict):
    """Email address format is receipts+{22-char-urlsafe-token}@receipts.cartsnitch.com."""
    response = await client.get(
        "/api/v1/me/email-in-address",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    email = data["email_address"]
    # Format: receipts+<22-char-urlsafe-token>@receipts.cartsnitch.com
    assert email.startswith("receipts+")
    assert email.endswith("@receipts.cartsnitch.com")
    # token_urlsafe(16) produces 22 chars
    middle = email[len("receipts+") : -len("@receipts.cartsnitch.com")]
    assert len(middle) == 22
    assert "@" not in middle
