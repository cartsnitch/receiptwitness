"""Async worker that consumes email receipt jobs from DragonflyDB Streams."""

import asyncio
import logging

from sqlalchemy import select

from receiptwitness.config import settings
from receiptwitness.events import publish_receipt_ingested
from receiptwitness.parsers.email.base import BaseEmailParser, EmailReceipt
from receiptwitness.parsers.email.detector import detect_retailer
from receiptwitness.parsers.email.kroger import KrogerEmailParser
from receiptwitness.parsers.email.meijer import MeijerEmailParser
from receiptwitness.parsers.email.target import TargetEmailParser
from receiptwitness.queue.email import ack_email, consume_emails, get_redis
from receiptwitness.shared.database import get_async_session_factory
from receiptwitness.shared.models import User

logger = logging.getLogger(__name__)

CONSUMER_NAME = "worker-1"

# Registry of available email parsers
PARSERS: dict[str, BaseEmailParser] = {
    "meijer": MeijerEmailParser(),
    "kroger": KrogerEmailParser(),
    "target": TargetEmailParser(),
}


async def resolve_user(token: str) -> str | None:
    """Look up user_id from email_inbound_token."""
    session_factory = get_async_session_factory(settings.database_url)
    async with session_factory() as session:
        result = await session.execute(select(User.id).where(User.email_inbound_token == token))
        row = result.scalar_one_or_none()
        return str(row) if row else None


async def process_job(msg_id: str, job) -> bool:
    """Process a single email job. Returns True on success."""
    # 1. Resolve user from token
    user_id = await resolve_user(job.user_id)  # user_id field holds token
    if not user_id:
        logger.warning("Unknown token %s, dropping message %s", job.user_id, msg_id)
        return True  # ack to avoid infinite retry

    # 2. Build EmailReceipt
    email = EmailReceipt(
        sender=job.sender,
        recipient=job.recipient,
        subject=job.subject,
        body_html=job.body_html,
        body_plain=job.body_plain,
        received_at=job.received_at,
    )

    # 3. Detect retailer
    retailer = detect_retailer(email)
    if not retailer or retailer not in PARSERS:
        logger.warning(
            "Unrecognized retailer from %s, archiving msg %s",
            job.sender,
            msg_id,
        )
        return True  # ack — no parser available

    # 4. Parse
    parser = PARSERS[retailer]
    parsed = parser.parse(email)

    # 5. Publish event
    await publish_receipt_ingested(
        user_id=user_id,
        store_slug=retailer,
        purchase_id=parsed.get("receipt_id", msg_id),
        purchase_date=parsed.get("purchase_date", ""),
        item_count=len(parsed.get("items", [])),
        total=parsed.get("total", 0),
    )
    return True


async def run_worker() -> None:
    """Main worker loop — consume and process email jobs."""
    client = await get_redis()
    logger.info("Email worker started, consuming from email:receipts")
    while True:
        try:
            jobs = await consume_emails(client, CONSUMER_NAME, count=5, block_ms=5000)
            for msg_id, job in jobs:
                try:
                    success = await process_job(msg_id, job)
                    if success:
                        await ack_email(client, msg_id)
                except Exception:
                    logger.exception("Failed to process email job %s", msg_id)
        except Exception:
            logger.exception("Worker loop error, retrying in 5s")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
