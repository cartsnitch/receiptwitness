"""Publish receipt ingestion events to Redis/DragonflyDB pub/sub."""

import json
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy import select

from receiptwitness.config import settings
from receiptwitness.notifications.email import send_receipt_notification
from receiptwitness.shared.database import get_async_session_factory
from receiptwitness.shared.models import User

logger = logging.getLogger(__name__)

CHANNEL_RECEIPTS_INGESTED = "cartsnitch.receipts.ingested"

# Module-level connection pool — shared across all publish calls
_pool: aioredis.ConnectionPool | None = None


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def _get_pool() -> aioredis.ConnectionPool:
    """Get or create the shared Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.redis_url, decode_responses=True, max_connections=10
        )
    return _pool


async def get_redis_client() -> aioredis.Redis:
    """Create an async Redis/DragonflyDB client with connection pooling."""
    return aioredis.Redis(connection_pool=_get_pool())


async def _send_notification_for_event(payload: dict) -> None:
    """Look up user email and send receipt notification. Silently skips on error."""
    try:
        user_uuid = uuid.UUID(payload["user_id"])
    except (ValueError, KeyError):
        logger.warning("Invalid user_id in event payload: %s", payload.get("user_id"))
        return

    try:
        session_factory = get_async_session_factory(settings.database_url)
        async with session_factory() as session:
            result = await session.execute(select(User.email).where(User.id == user_uuid))
            row = result.scalar_one_or_none()
            if not row:
                logger.warning("User %s not found for notification", user_uuid)
                return
            user_email = row
    except Exception:
        logger.exception("Failed to look up user email for notification")
        return

    await send_receipt_notification(
        user_email=user_email,
        store_name=payload["store_slug"],
        item_count=payload["item_count"],
        total=payload["total"],
        purchase_date=payload["purchase_date"],
    )


async def publish_receipt_ingested(
    user_id: str,
    store_slug: str,
    purchase_id: str,
    purchase_date: str,
    item_count: int,
    total: Decimal | float,
) -> None:
    """Publish a cartsnitch.receipts.ingested event after successful ingestion."""
    payload = {
        "user_id": user_id,
        "store_slug": store_slug,
        "purchase_id": purchase_id,
        "purchase_date": purchase_date,
        "item_count": item_count,
        "total": float(total) if isinstance(total, Decimal) else total,
    }
    event = {
        "event_type": CHANNEL_RECEIPTS_INGESTED,
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "receiptwitness",
        "payload": payload,
    }

    try:
        client = await get_redis_client()
        await client.publish(CHANNEL_RECEIPTS_INGESTED, json.dumps(event, cls=_DecimalEncoder))
        logger.info(
            "Published %s event for purchase %s",
            CHANNEL_RECEIPTS_INGESTED,
            purchase_id,
        )
    except aioredis.ConnectionError:
        logger.error("Failed to publish event — Redis/DragonflyDB connection error")
        raise
    else:
        await _send_notification_for_event(payload)
