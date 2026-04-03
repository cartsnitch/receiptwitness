"""Email notifications via Resend."""

import asyncio
import html
import logging

import resend

from receiptwitness.config import settings

logger = logging.getLogger(__name__)


async def send_receipt_notification(
    user_email: str,
    store_name: str,
    item_count: int,
    total: float,
    purchase_date: str,
) -> None:
    """Send receipt ingestion confirmation email via Resend."""
    if not settings.notifications_enabled or not settings.resend_api_key:
        logger.debug("Notifications disabled — skipping email send")
        return

    resend.api_key = settings.resend_api_key
    store_name_safe = html.escape(store_name)
    purchase_date_safe = html.escape(purchase_date)
    try:
        await asyncio.to_thread(
            resend.Emails.send,
            {
                "from": settings.notification_email_from,
                "to": [user_email],
                "subject": f"Receipt processed: {store_name} - ${total:.2f}",
                "html": (
                    f"<p>Your receipt from <strong>{store_name_safe}</strong> on "
                    f"{purchase_date_safe} has been processed.</p>"
                    f"<p>{item_count} items, total: ${total:.2f}</p>"
                ),
            },
        )
        logger.info("Receipt notification sent to %s", user_email)
    except Exception:
        logger.exception("Failed to send receipt notification to %s", user_email)
