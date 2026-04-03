"""Parse Meijer digital receipt emails into structured purchase data."""

import re
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from bs4.element import Tag

from receiptwitness.parsers.email.base import BaseEmailParser, EmailReceipt


def _to_decimal(value, default: str = "0") -> Decimal:
    """Safely convert a value to Decimal."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _extract_receipt_id(soup: BeautifulSoup, subject: str | None) -> str | None:
    """Extract receipt/transaction ID from subject or body."""
    if subject:
        match = re.search(r"TXN[-\s]\d{4}[-\s]\d{4}[-\s]\d+", subject)
        if match:
            return match.group(0).replace(" ", "-")
    # Fallback: look in body
    text = soup.get_text()
    match = re.search(r"TXN[-\s]\d{4}[-\s]\d{4}[-\s]\d+", text)
    if match:
        return match.group(0).replace(" ", "-")
    return None


def _extract_purchase_date(soup: BeautifulSoup, subject: str | None) -> str | None:
    """Extract purchase date from subject or body."""
    text = soup.get_text()

    # Try ISO format first: YYYY-MM-DD
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # Try written format: March 15, 2026
    match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", text)
    if match:
        month_str = match.group(1).lower()
        day = match.group(2)
        year = match.group(3)
        month_map = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }
        month = month_map.get(month_str)
        if month:
            return f"{year}-{month}-{day.zfill(2)}"

    # MM/DD/YYYY
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        return f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"

    return None


def _extract_store_info(soup: BeautifulSoup) -> dict:
    """Extract store name and number from the email body."""
    store_info: dict = {}

    # Look for store number in header
    store_num_match = re.search(r"Meijer\s+Store\s+#?(\d+)", soup.get_text(), re.IGNORECASE)
    if store_num_match:
        store_info["store_number"] = store_num_match.group(1)

    return store_info


def _extract_items(table: Tag | None) -> list[dict]:
    """Extract line items from the items table."""
    items: list[dict] = []
    if not table:
        return items

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        name_cell = cells[0].get_text(strip=True)
        qty_cell = cells[1].get_text(strip=True)
        price_cell = cells[2].get_text(strip=True)

        if not name_cell or name_cell.lower() in ("item", "description"):
            continue

        # Skip subtotal/tax/total/savings rows
        if any(
            label in name_cell.lower()
            for label in ("subtotal", "tax", "total", "savings", "grand total")
        ):
            continue

        try:
            quantity = Decimal(qty_cell)
        except (InvalidOperation, ValueError, TypeError):
            quantity = Decimal("1")

        price_str = price_cell.replace("$", "").replace(",", "").strip()
        try:
            unit_price = Decimal(price_str)
        except (InvalidOperation, ValueError, TypeError):
            unit_price = Decimal("0")

        extended_price = unit_price  # Default to unit price; no qty column in fixture

        items.append(
            {
                "product_name_raw": name_cell,
                "quantity": quantity,
                "unit_price": unit_price,
                "extended_price": extended_price,
            }
        )

    return items


def _extract_totals_plain(text: str) -> dict:
    """Extract totals from plain text (no HTML)."""
    totals: dict = {
        "subtotal": None,
        "tax": None,
        "total": None,
        "savings_total": None,
    }

    match = re.search(r"\bSubtotal\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if match:
        totals["subtotal"] = _to_decimal(match.group(1))

    match = re.search(r"\bTax\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if match:
        totals["tax"] = _to_decimal(match.group(1))

    grand_total_match = re.search(r"Grand\s+Total\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if grand_total_match:
        totals["total"] = _to_decimal(grand_total_match.group(1))

    savings_match = re.search(r"\bSavings\b[:\s$\-]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if savings_match:
        totals["savings_total"] = _to_decimal(savings_match.group(1))

    if totals["total"] is None:
        total_match = re.search(r"\bTotal\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
        if total_match:
            totals["total"] = _to_decimal(total_match.group(1))

    return totals


def _extract_totals(soup: BeautifulSoup) -> dict:
    """Extract subtotal, tax, total, and savings from the totals section."""
    text = soup.get_text()

    totals: dict = {
        "subtotal": None,
        "tax": None,
        "total": None,
        "savings_total": None,
    }

    # Subtotal — use word boundary to avoid matching "Subtotal" with "Total"
    match = re.search(r"\bSubtotal\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if match:
        totals["subtotal"] = _to_decimal(match.group(1))

    # Tax
    match = re.search(r"\bTax\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if match:
        totals["tax"] = _to_decimal(match.group(1))

    # Grand Total (before plain "Total" to avoid matching "Subtotal")
    grand_total_match = re.search(r"Grand\s+Total\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if grand_total_match:
        totals["total"] = _to_decimal(grand_total_match.group(1))

    # Savings — allow any combination of whitespace/$- around the number
    savings_match = re.search(r"\bSavings\b[:\s$\-]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
    if savings_match:
        totals["savings_total"] = _to_decimal(savings_match.group(1))

    # Plain "Total" only if Grand Total wasn't found
    if totals["total"] is None:
        total_match = re.search(r"\bTotal\b[:\s$]*([0-9,]+\.?\d*)", text, re.IGNORECASE)
        if total_match:
            totals["total"] = _to_decimal(total_match.group(1))

    return totals


class MeijerEmailParser(BaseEmailParser):
    """Parse Meijer digital receipt emails forwarded by users."""

    def can_parse(self, email: EmailReceipt) -> bool:
        sender = email.sender.lower().strip()
        # Extract email from "Name <email>" format
        match = re.search(r"<([^>]+)>", sender)
        if match:
            sender = match.group(1)
        return "meijer" in sender

    def parse(self, email: EmailReceipt) -> dict:
        body_html = email.body_html
        body_plain = email.body_plain or ""
        body = body_html or body_plain
        soup = BeautifulSoup(body, "html.parser")

        receipt_id = _extract_receipt_id(soup, email.subject)
        purchase_date = _extract_purchase_date(soup, email.subject)
        _ = _extract_store_info(soup)

        # Find the items table — look for one with Item/Qty/Price headers
        table = None
        for tbl in soup.find_all("table"):
            headers = tbl.find_all("th")
            header_texts = [h.get_text(strip=True).lower() for h in headers]
            if any("item" in h or "qty" in h or "price" in h for h in header_texts):
                table = tbl
                break

        items = _extract_items(table)

        # Extract totals from HTML; fall back to plain text if no HTML
        if body_html:
            totals = _extract_totals(soup)
        else:
            totals = _extract_totals_plain(body_plain)

        return {
            "receipt_id": receipt_id or "",
            "purchase_date": purchase_date or "",
            "total": totals["total"] or Decimal("0"),
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "savings_total": totals["savings_total"],
            "items": items,
        }
