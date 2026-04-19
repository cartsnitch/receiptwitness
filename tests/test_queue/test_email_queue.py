"""Tests for email queue using DragonflyDB Streams."""

import pytest
from fakeredis import aioredis as fake_aioredis

from receiptwitness.queue.email import (
    CONSUMER_GROUP,
    STREAM_KEY,
    EmailJob,
    ack_email,
    consume_emails,
    enqueue_email,
    ensure_consumer_group,
)


@pytest.fixture
async def fake_client():
    """Yield a fake async Redis client."""
    client = fake_aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def sample_job():
    """Sample EmailJob for testing."""
    return EmailJob(
        user_id="user-123",
        sender="no-reply@kroger.com",
        recipient="user@example.com",
        subject="Kroger Receipt",
        body_html="<html><body>Receipt</body></html>",
        body_plain="Receipt",
        received_at="2026-04-01T12:00:00Z",
        message_id="msg-abc-123",
    )


@pytest.mark.asyncio
async def test_enqueue_and_consume(fake_client, sample_job):
    """Enqueue a job, consume it, verify fields match."""
    msg_id = await enqueue_email(fake_client, sample_job)
    assert msg_id is not None

    consumed = await consume_emails(fake_client, "test-worker", count=1, block_ms=100)
    assert len(consumed) == 1
    consumed_id, consumed_job = consumed[0]
    assert consumed_id == msg_id
    assert consumed_job.user_id == sample_job.user_id
    assert consumed_job.sender == sample_job.sender
    assert consumed_job.recipient == sample_job.recipient
    assert consumed_job.subject == sample_job.subject
    assert consumed_job.message_id == sample_job.message_id


@pytest.mark.asyncio
async def test_ack_removes_from_pending(fake_client, sample_job):
    """After ack, message is no longer pending."""
    msg_id = await enqueue_email(fake_client, sample_job)

    # Consume the message (moves it to pending)
    consumed = await consume_emails(fake_client, "test-worker", count=1, block_ms=100)
    assert len(consumed) == 1

    # Acknowledge it
    await ack_email(fake_client, msg_id)

    # Check pending count for this consumer group
    pending = await fake_client.xpending(STREAM_KEY, CONSUMER_GROUP)
    assert pending is None or pending["pending"] == 0


@pytest.mark.asyncio
async def test_ensure_consumer_group_idempotent(fake_client):
    """Calling ensure_consumer_group twice does not error."""
    await ensure_consumer_group(fake_client)
    # Calling again should not raise
    await ensure_consumer_group(fake_client)
