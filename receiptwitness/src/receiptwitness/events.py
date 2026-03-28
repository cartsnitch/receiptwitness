"""Publish receipt ingestion events to Redis/DragonflyDB pub/sub."""

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal

import redis.asyncio as aioredis

from receiptwitness.config import settings

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


async def publish_receipt_ingested(
    user_id: str,
    store_slug: str,
    purchase_id: str,
    purchase_date: str,
    item_count: int,
    total: Decimal | float,
) -> None:
    """Publish a cartsnitch.receipts.ingested event after successful ingestion."""
    event = {
        "event_type": CHANNEL_RECEIPTS_INGESTED,
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "receiptwitness",
        "payload": {
            "user_id": user_id,
            "store_slug": store_slug,
            "purchase_id": purchase_id,
            "purchase_date": purchase_date,
            "item_count": item_count,
            "total": float(total) if isinstance(total, Decimal) else total,
        },
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
