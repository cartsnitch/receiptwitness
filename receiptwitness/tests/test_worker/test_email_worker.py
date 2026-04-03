"""Tests for email_worker."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fakeredis import aioredis as fake_aioredis

from receiptwitness.parsers.email.base import EmailReceipt
from receiptwitness.queue.email import (
    EmailJob,
)
from receiptwitness.worker.email_worker import (
    process_job,
    resolve_user,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def fake_redis():
    """Fake async Redis client for queue testing."""
    client = fake_aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def sample_email_job():
    """Sample EmailJob matching DragonflyDB queue schema."""
    return EmailJob(
        user_id="token-abc-123",
        sender="no-reply@meijer.com",
        recipient="user@example.com",
        subject="Your Meijer Receipt",
        body_html="<html><body>Total: $42.00</body></html>",
        body_plain="Total: $42.00",
        received_at="2026-04-01T12:00:00Z",
        message_id="msg-xyz-789",
    )


@pytest.fixture
def sample_email():
    """Sample EmailReceipt for parser testing."""
    return EmailReceipt(
        sender="no-reply@meijer.com",
        recipient="user@example.com",
        subject="Your Meijer Receipt",
        body_html="<html><body>Total: $42.00<br/>Receipt #12345</body></html>",
        body_plain="Total: $42.00",
        received_at="2026-04-01T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# resolve_user tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_user_valid_token():
    """Valid token returns user_id string."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "user-uuid-42"
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    factory = MagicMock(return_value=mock_session)

    with patch(
        "receiptwitness.worker.email_worker.get_async_session_factory",
        return_value=factory,
    ):
        user_id = await resolve_user("token-abc-123")

    assert user_id == "user-uuid-42"
    factory.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_user_invalid_token():
    """Invalid token returns None."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    factory = MagicMock(return_value=mock_session)

    with patch(
        "receiptwitness.worker.email_worker.get_async_session_factory",
        return_value=factory,
    ):
        user_id = await resolve_user("bad-token")

    assert user_id is None


# ---------------------------------------------------------------------------
# process_job tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_job_unknown_retailer(sample_email_job):
    """Unknown retailer logs warning and returns True (ack, no retry)."""
    unknown_job = EmailJob(
        user_id="token-abc-123",
        sender="no-reply@unknownretailer.com",
        recipient="user@example.com",
        subject="Receipt",
        body_html="<html></html>",
        body_plain="",
        received_at="2026-04-01T12:00:00Z",
        message_id="msg-xyz-789",
    )

    with (
        patch(
            "receiptwitness.worker.email_worker.resolve_user",
            return_value="user-uuid-42",
        ),
        patch(
            "receiptwitness.worker.email_worker.publish_receipt_ingested",
            new_callable=AsyncMock,
        ) as mock_publish,
    ):
        result = await process_job("msg-id-1", unknown_job)

    assert result is True
    mock_publish.assert_not_called()


@pytest.mark.asyncio
async def test_process_job_success(sample_email_job, sample_email):
    """Known retailer: full pipeline runs — parse, normalize, publish event."""
    parsed_data = {
        "receipt_id": "RCP-999",
        "purchase_date": "2026-04-01",
        "total": Decimal("42.00"),
        "items": [
            {
                "product_name_raw": "ORGANIC BANANAS",
                "quantity": Decimal("1"),
                "unit_price": Decimal("0.69"),
                "extended_price": Decimal("0.69"),
            },
        ],
    }

    mock_parser = MagicMock()
    mock_parser.parse.return_value = parsed_data

    with (
        patch(
            "receiptwitness.worker.email_worker.resolve_user",
            return_value="user-uuid-42",
        ),
        patch.dict(
            "receiptwitness.worker.email_worker.PARSERS",
            {"meijer": mock_parser},
            clear=False,
        ),
        patch(
            "receiptwitness.worker.email_worker.publish_receipt_ingested",
            new_callable=AsyncMock,
        ) as mock_publish,
    ):
        result = await process_job("msg-id-1", sample_email_job)

    assert result is True
    mock_parser.parse.assert_called_once()
    mock_publish.assert_called_once_with(
        user_id="user-uuid-42",
        store_slug="meijer",
        purchase_id="RCP-999",
        purchase_date="2026-04-01",
        item_count=1,
        total=Decimal("42.00"),
    )
