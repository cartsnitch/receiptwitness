"""Kroger email receipt parser."""

import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from receiptwitness.parsers.email.base import BaseEmailParser, EmailReceipt

logger = logging.getLogger(__name__)


def _to_decimal(value: str | float | int | None, default: Decimal = Decimal("0")) -> Decimal:
    """Safely convert a value to Decimal."""
    if value is None:
        return default
    try:
        return Decimal(str(value).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return default


def _extract_total(body: str) -> Decimal:
    """Extract the transaction total from email body."""
    patterns = [
        r"Total[:\s]*\$?([0-9,]+\.[0-9]{2})",
        r"Amount[:\s]*\$?([0-9,]+\.[0-9]{2})",
        r"Grand\s+Total[:\s]*\$?([0-9,]+\.[0-9]{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return _to_decimal(match.group(1))
    return Decimal("0")


def _extract_receipt_id(body: str) -> str | None:
    """Extract receipt ID / transaction ID from HTML body.

    Strips HTML tags first so that whitespace between delimiters and values
    (e.g. from ``</strong> KR-2026-0315-4829`` -> `` KR-2026-0315-4829``)
    is normalized and the pattern can match cleanly.
    """
    stripped = re.sub(r"<[^>]+>", "", body)
    patterns = [
        r"Receipt\s*#[:\s]*([A-Z0-9-]+)",
        r"Transaction\s*#[:\s]*([A-Z0-9-]+)",
        r"Order\s*#[:\s]*([A-Z0-9-]+)",
        r"Confirmation\s*#[:\s]*([A-Z0-9-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, stripped, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _extract_date(body: str) -> str:
    """Extract purchase date from email body. Returns ISO date string or empty string."""
    patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body)
        if match:
            raw = match.group(1)
            try:
                dt = datetime.strptime(raw.replace(",", ""), "%b %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
            try:
                for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y"):
                    try:
                        dt = datetime.strptime(raw, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            except Exception:
                pass
    return ""


def _extract_items_soup(body: str) -> list[dict]:
    """Extract line items from HTML email body using BeautifulSoup."""
    items = []
    try:
        soup = BeautifulSoup(body, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        # Strip HTML tags from raw body to normalize whitespace
        stripped = re.sub(r"<[^>]+>", " ", body)
        stripped = re.sub(r"\s+", " ", stripped)
        skip_prefixes = (
            "Subtotal",
            "Tax",
            "Total",
            "Kroger",
            "Target",
            "Date",
            "Receipt",
            "Order",
            "Transaction",
            "Confirmation",
            "Thank",
            "Questions",
            "Keep",
            "Receipt",
        )
        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith(skip_prefixes):
                continue
            # Match lines like "Product Name $9.99"
            match = re.match(r"(.+?)\s+\$([0-9]+\.[0-9]{2})\s*$", line)
            if match:
                name = match.group(1).strip()
                price = _to_decimal(match.group(2))
                if len(name) > 2 and price > 0:
                    items.append(
                        {
                            "product_name_raw": name,
                            "quantity": Decimal("1"),
                            "unit_price": price,
                            "extended_price": price,
                        }
                    )
    except Exception:
        pass
    return items[:20]


class KrogerEmailParser(BaseEmailParser):
    """Parse Kroger email receipts (digital receipts via kroger.com)."""

    KROGER_KEYWORDS = ("kroger", "kroger.com", "plus")

    def can_parse(self, email: EmailReceipt) -> bool:
        sender = (email.sender or "").lower()
        body = (email.body_html or email.body_plain or "").lower()
        return any(kw in sender or kw in body for kw in self.KROGER_KEYWORDS)

    def parse(self, email: EmailReceipt) -> dict:
        body = (email.body_html or email.body_plain or "").strip()
        total = _extract_total(body)
        receipt_id = _extract_receipt_id(body) or ""
        purchase_date = _extract_date(body)
        items = _extract_items_soup(body)

        return {
            "receipt_id": receipt_id,
            "purchase_date": purchase_date,
            "total": total,
            "items": items,
        }
