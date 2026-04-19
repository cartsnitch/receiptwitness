"""Internal API routes for triggering scrapes and checking status."""

import hashlib
import hmac
import re
import time

from fastapi import APIRouter, HTTPException, Request

from receiptwitness.config import settings
from receiptwitness.queue.email import EmailJob, enqueue_email, get_redis

router = APIRouter()

TOKEN_PATTERN = re.compile(r"receipts\+([A-Za-z0-9_-]+)@")


def verify_mailgun_signature(token: str, timestamp: str, signature: str) -> bool:
    """Verify Mailgun webhook signature."""
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False
    if abs(time.time() - ts) > 300:  # 5 min freshness
        return False
    key = settings.mailgun_webhook_signing_key.encode()
    hmac_digest = hmac.new(key, f"{timestamp}{token}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, hmac_digest)


@router.post("/inbound/email")
async def receive_inbound_email(request: Request):
    form = await request.form()
    # 1. Verify Mailgun signature
    token = str(form.get("token", ""))
    timestamp = str(form.get("timestamp", ""))
    signature = str(form.get("signature", ""))
    if not verify_mailgun_signature(token, timestamp, signature):
        raise HTTPException(status_code=406, detail="Invalid signature")
    # 2. Extract account token from recipient
    recipient = str(form.get("recipient", ""))
    match = TOKEN_PATTERN.search(recipient)
    if not match:
        raise HTTPException(status_code=406, detail="Invalid recipient")
    account_token = match.group(1)
    # 3. Enqueue — worker resolves token -> user_id
    body_html_val = form.get("body-html")
    body_plain_val = form.get("body-plain")
    job = EmailJob(
        user_id=account_token,
        sender=str(form.get("sender", "")),
        recipient=recipient,
        subject=str(form.get("subject", "")),
        body_html=str(body_html_val) if body_html_val is not None else None,
        body_plain=str(body_plain_val) if body_plain_val is not None else None,
        received_at=str(form.get("timestamp", "")),
        message_id=str(form.get("Message-Id", "")),
    )
    client = await get_redis()
    await enqueue_email(client, job)
    return {"status": "queued"}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "receiptwitness"}
