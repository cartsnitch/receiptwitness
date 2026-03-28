"""Integration tests for alert endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_alerts_empty(client, auth_headers):
    """No purchases means no alerts."""
    resp = await client.get("/alerts", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_alert_settings(client, auth_headers):
    resp = await client.get("/alerts/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["price_increase_threshold_pct"] == 5.0
    assert data["shrinkflation_enabled"] is True
    assert data["email_notifications"] is False


@pytest.mark.asyncio
async def test_update_alert_settings_returns_501(client, auth_headers):
    resp = await client.put(
        "/alerts/settings",
        headers=auth_headers,
        json={
            "price_increase_threshold_pct": 10.0,
            "shrinkflation_enabled": False,
            "email_notifications": True,
        },
    )
    assert resp.status_code == 501
