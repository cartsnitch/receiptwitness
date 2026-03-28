"""Tests for structured error responses and error monitoring."""

import pytest


@pytest.mark.asyncio
async def test_404_returns_structured_error(client):
    """Non-existent route should return structured error."""
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "code" in body
    assert body["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_validation_error_returns_422_with_field_errors(client):
    """Invalid request body should return structured validation errors."""
    resp = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "short", "display_name": ""},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0
    # Each error should have field, message, type
    for err in body["errors"]:
        assert "field" in err
        assert "message" in err
        assert "type" in err


@pytest.mark.asyncio
async def test_error_stats_requires_service_key(client):
    """Error stats endpoint should require X-Service-Key."""
    resp = await client.get("/internal/error-stats")
    assert resp.status_code == 422  # Missing required header


@pytest.mark.asyncio
async def test_error_stats_with_valid_key(client):
    """Error stats endpoint returns monitoring data with valid key."""
    resp = await client.get(
        "/internal/error-stats",
        headers={"X-Service-Key": "change-me-in-production"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "error_counts" in body
    assert "recent_5xx_count" in body
