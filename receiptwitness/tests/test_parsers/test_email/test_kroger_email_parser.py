"""Tests for KrogerEmailParser."""

from pathlib import Path

from receiptwitness.parsers.email.base import EmailReceipt
from receiptwitness.parsers.email.kroger import KrogerEmailParser

FIXTURE_PATH = Path(__file__).parent.parent.parent / "fixtures" / "kroger_email_receipt.html"


class TestKrogerEmailParser:
    """Tests for KrogerEmailParser."""

    def setup_method(self) -> None:
        self.parser = KrogerEmailParser()
        self.fixture_html = FIXTURE_PATH.read_text()

    def test_can_parse_kroger_sender(self) -> None:
        email = EmailReceipt(
            sender="noreply@email.kroger.com",
            recipient="user@example.com",
            subject="Your Kroger Receipt",
            body_html=self.fixture_html,
        )
        assert self.parser.can_parse(email) is True

    def test_can_parse_kroger_in_body(self) -> None:
        email = EmailReceipt(
            sender="someone@unknown.com",
            recipient="user@example.com",
            subject="Your Receipt",
            body_html="<html><body>Kroger digital receipt</body></html>",
        )
        assert self.parser.can_parse(email) is True

    def test_cannot_parse_unrelated(self) -> None:
        email = EmailReceipt(
            sender="noreply@walmart.com",
            recipient="user@example.com",
            subject="Your Receipt",
            body_html="<html><body>Walmart receipt</body></html>",
        )
        assert self.parser.can_parse(email) is False

    def test_parse_items(self) -> None:
        email = EmailReceipt(
            sender="noreply@kroger.com",
            recipient="user@example.com",
            subject="Your Kroger Receipt",
            body_html=self.fixture_html,
        )
        result = self.parser.parse(email)
        items = result.get("items", [])
        assert len(items) >= 3
        product_names = [item["product_name_raw"] for item in items]
        assert any("Whole Milk" in name for name in product_names)
        assert any("Sourdough" in name for name in product_names)
        for item in items:
            assert "unit_price" in item
            assert "extended_price" in item

    def test_parse_totals(self) -> None:
        email = EmailReceipt(
            sender="noreply@kroger.com",
            recipient="user@example.com",
            subject="Your Kroger Receipt",
            body_html=self.fixture_html,
        )
        result = self.parser.parse(email)
        total = result.get("total", 0)
        assert total > 0

    def test_parse_receipt_id(self) -> None:
        email = EmailReceipt(
            sender="noreply@kroger.com",
            recipient="user@example.com",
            subject="Your Kroger Receipt",
            body_html=self.fixture_html,
        )
        result = self.parser.parse(email)
        receipt_id = result.get("receipt_id", "")
        assert "KR-2026" in receipt_id or "TXN" in receipt_id

    def test_parse_date(self) -> None:
        email = EmailReceipt(
            sender="noreply@kroger.com",
            recipient="user@example.com",
            subject="Your Kroger Receipt",
            body_html=self.fixture_html,
        )
        result = self.parser.parse(email)
        purchase_date = result.get("purchase_date", "")
        assert purchase_date == "2026-03-15"
