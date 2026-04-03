"""DragonflyDB Streams queue for email receipt processing."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import cast

import redis.asyncio as aioredis

from receiptwitness.config import settings

logger = logging.getLogger(__name__)

STREAM_KEY = "email:receipts"
CONSUMER_GROUP = "email-workers"


@dataclass
class EmailJob:
    """Payload for an email receipt processing job."""

    user_id: str
    sender: str
    recipient: str
    subject: str
    body_html: str | None
    body_plain: str | None
    received_at: str
    message_id: str  # from email provider, for dedup


async def get_redis() -> aioredis.Redis:
    """Get async Redis/DragonflyDB client."""
    return cast(aioredis.Redis, aioredis.from_url(settings.redis_url, decode_responses=True))


async def ensure_consumer_group(client: aioredis.Redis) -> None:
    """Create consumer group if it does not exist."""
    try:
        await client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except aioredis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


async def enqueue_email(client: aioredis.Redis, job: EmailJob) -> str:
    """Add email job to the stream. Returns the stream message ID."""
    payload: dict[str, str | bytes | int | float] = {"data": json.dumps(asdict(job))}
    msg_id: str = cast(str, await client.xadd(STREAM_KEY, payload))  # type: ignore[arg-type]  # redis-py StreamCommands.xadd expects broader FieldT union; runtime behavior is correct
    logger.info("Enqueued email job %s for user %s", msg_id, job.user_id)
    return msg_id


async def consume_emails(
    client: aioredis.Redis,
    consumer_name: str,
    count: int = 1,
    block_ms: int = 5000,
) -> list[tuple[str, EmailJob]]:
    """Read pending messages from the stream. Returns list of (msg_id, EmailJob)."""
    await ensure_consumer_group(client)
    messages = await client.xreadgroup(
        CONSUMER_GROUP, consumer_name, {STREAM_KEY: ">"}, count=count, block=block_ms
    )
    results = []
    for _stream, entries in messages:
        for msg_id, fields in entries:
            job = EmailJob(**json.loads(fields["data"]))
            results.append((msg_id, job))
    return results


async def ack_email(client: aioredis.Redis, msg_id: str) -> None:
    """Acknowledge a processed message."""
    await client.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
