"""Tests for the /inbound/email webhook endpoint."""

import hashlib
import hmac
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from receiptwitness.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_redis():
    redis_mock = AsyncMock()
    with patch("receiptwitness.api.routes.get_redis", return_value=redis_mock):
        enqueue_patcher = patch("receiptwitness.api.routes.enqueue_email", new_callable=AsyncMock)
        with enqueue_patcher as mock_enqueue:
            yield {"redis": redis_mock, "enqueue": mock_enqueue}


def make_signature(signing_key: str, token: str, timestamp: str) -> str:
    return hmac.new(
        signing_key.encode(),
        f"{timestamp}{token}".encode(),
        hashlib.sha256,
    ).hexdigest()


def valid_form(signing_key: str = "test-secret"):
    ts = str(int(time.time()))
    token = "test-token"
    sig = make_signature(signing_key, token, ts)
    return {
        "token": token,
        "timestamp": ts,
        "signature": sig,
        "sender": "sender@example.com",
        "recipient": "receipts+user123@example.com",
        "subject": "Your Meijer Receipt",
        "body-html": "<p>Thank you for shopping at Meijer</p>",
        "body-plain": "Thank you for shopping at Meijer",
        "Message-Id": "<msg-001@example.com>",
    }


def test_valid_webhook(client, mock_redis):
    with patch("receiptwitness.api.routes.settings") as mock_settings:
        mock_settings.mailgun_webhook_signing_key = "test-secret"
        response = client.post("/inbound/email", data=valid_form())
    assert response.status_code == 200
    assert response.json() == {"status": "queued"}
    mock_redis["enqueue"].assert_awaited_once()


def test_invalid_signature(client, mock_redis):
    with patch("receiptwitness.api.routes.settings") as mock_settings:
        mock_settings.mailgun_webhook_signing_key = "test-secret"
        form = valid_form()
        form["signature"] = "wrong-signature"
        response = client.post("/inbound/email", data=form)
    assert response.status_code == 406
    assert response.json()["detail"] == "Invalid signature"
    mock_redis["enqueue"].assert_not_awaited()


def test_invalid_recipient_no_plus(client, mock_redis):
    with patch("receiptwitness.api.routes.settings") as mock_settings:
        mock_settings.mailgun_webhook_signing_key = "test-secret"
        form = valid_form()
        form["recipient"] = "receipts@example.com"  # no plus-address
        response = client.post("/inbound/email", data=form)
    assert response.status_code == 406
    assert response.json()["detail"] == "Invalid recipient"
    mock_redis["enqueue"].assert_not_awaited()


def test_stale_timestamp(client, mock_redis):
    with patch("receiptwitness.api.routes.settings") as mock_settings:
        mock_settings.mailgun_webhook_signing_key = "test-secret"
        ts = str(int(time.time()) - 600)  # 10 min old
        token = "test-token"
        sig = make_signature("test-secret", token, ts)
        form = {
            "token": token,
            "timestamp": ts,
            "signature": sig,
            "sender": "sender@example.com",
            "recipient": "receipts+user123@example.com",
            "subject": "Receipt",
        }
        response = client.post("/inbound/email", data=form)
    assert response.status_code == 406
    assert response.json()["detail"] == "Invalid signature"
    mock_redis["enqueue"].assert_not_awaited()


def test_invalid_timestamp_returns_406(client, mock_redis):
    """Empty timestamp should return 406, not 500."""
    with patch("receiptwitness.api.routes.settings") as mock_settings:
        mock_settings.mailgun_webhook_signing_key = "test-secret"
        form = {
            "token": "test-token",
            "timestamp": "",
            "signature": "any-sig",
            "sender": "sender@example.com",
            "recipient": "receipts+user123@example.com",
            "subject": "Receipt",
        }
        response = client.post("/inbound/email", data=form)
    assert response.status_code == 406
    assert response.json()["detail"] == "Invalid signature"
    mock_redis["enqueue"].assert_not_awaited()


def test_get_inbound_email_returns_405(client):
    """GET /inbound/email is not allowed."""
    response = client.get("/inbound/email")
    assert response.status_code == 405
