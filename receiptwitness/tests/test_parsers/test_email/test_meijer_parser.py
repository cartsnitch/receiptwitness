"""Tests for the Meijer email receipt parser."""

import os
from decimal import Decimal

import pytest

from receiptwitness.parsers.email.base import EmailReceipt
from receiptwitness.parsers.email.meijer import MeijerEmailParser

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "fixtures", "meijer_email_receipt.html"
)


def load_fixture() -> str:
    with open(FIXTURE_PATH) as f:
        return f.read()


@pytest.fixture
def meijer_email() -> EmailReceipt:
    html = load_fixture()
    return EmailReceipt(
        sender="Meijer Receipts <receipts@email.meijer.com>",
        recipient="shopper@example.com",
        subject="Your Meijer Receipt — Transaction #TXN-2026-0315-0042",
        body_html=html,
        body_plain=None,
        received_at="2026-03-15T14:34:00Z",
    )


@pytest.fixture
def kroger_email() -> EmailReceipt:
    return EmailReceipt(
        sender="Kroger <noreply@email.kroger.com>",
        recipient="shopper@example.com",
        subject="Your Kroger Receipt",
        body_html="<html><body>Kroger receipt</body></html>",
    )


class TestCanParse:
    def test_can_parse_meijer(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        assert parser.can_parse(meijer_email) is True

    def test_cannot_parse_kroger(self, kroger_email: EmailReceipt):
        parser = MeijerEmailParser()
        assert parser.can_parse(kroger_email) is False

    def test_can_parse_meijer_plain_sender(self):
        email = EmailReceipt(
            sender="receipts@meijer.com",
            recipient="shopper@example.com",
            subject="Receipt",
            body_html="<html></html>",
        )
        parser = MeijerEmailParser()
        assert parser.can_parse(email) is True

    def test_cannot_parse_non_meijer(self):
        email = EmailReceipt(
            sender=" Target <no-reply@target.com>",
            recipient="shopper@example.com",
            subject="Target Receipt",
            body_html="<html></html>",
        )
        parser = MeijerEmailParser()
        assert parser.can_parse(email) is False


class TestParseMeijerReceipt:
    def test_receipt_id_extracted(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        result = parser.parse(meijer_email)
        assert result["receipt_id"] == "TXN-2026-0315-0042"

    def test_purchase_date_extracted(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        result = parser.parse(meijer_email)
        assert result["purchase_date"] == "2026-03-15"

    def test_items_extracted(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        result = parser.parse(meijer_email)
        items = result["items"]
        assert len(items) == 8

        names = [item["product_name_raw"] for item in items]
        assert "ORGANIC BANANAS" in names
        assert "WHOLE MILK 1 GAL" in names
        assert "GROUND BEEF 85/15 1LB" in names

    def test_item_quantities(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        result = parser.parse(meijer_email)
        # Find ORGANIC BANANAS
        bananas = next(i for i in result["items"] if "BANANAS" in i["product_name_raw"])
        assert bananas["quantity"] == Decimal("1")

    def test_item_prices(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        result = parser.parse(meijer_email)
        # Find ORGANIC BANANAS
        bananas = next(i for i in result["items"] if "BANANAS" in i["product_name_raw"])
        assert bananas["unit_price"] == Decimal("0.69")
        assert bananas["extended_price"] == Decimal("0.69")

    def test_totals(self, meijer_email: EmailReceipt):
        parser = MeijerEmailParser()
        result = parser.parse(meijer_email)
        assert result["total"] == Decimal("33.41")
        assert result["subtotal"] == Decimal("31.22")
        assert result["tax"] == Decimal("2.19")
        assert result["savings_total"] == Decimal("3.40")


class TestParseHandlesMissingFields:
    def test_missing_body_html_falls_back_to_plain(self):
        email = EmailReceipt(
            sender="receipts@email.meijer.com",
            recipient="shopper@example.com",
            subject="Your Meijer Receipt",
            body_html=None,
            body_plain="TXN-1234 | March 15, 2026 | Total: $10.00",
        )
        parser = MeijerEmailParser()
        result = parser.parse(email)
        # Should not raise, returns minimal result
        assert result["receipt_id"] == ""
        assert result["purchase_date"] == "2026-03-15"
        assert result["total"] == Decimal("10.00")

    def test_empty_email(self):
        email = EmailReceipt(
            sender="receipts@email.meijer.com",
            recipient="shopper@example.com",
            subject="Receipt",
            body_html="",
            body_plain="",
        )
        parser = MeijerEmailParser()
        result = parser.parse(email)
        assert result["receipt_id"] == ""
        assert result["purchase_date"] == ""
        assert result["total"] == Decimal("0")
        assert result["items"] == []

    def test_missing_subject_date_from_body(self):
        html = """
        <html>
          <body>
            <p>Thank you for shopping on April 1, 2026</p>
            <p>Total: $15.00</p>
          </body>
        </html>
        """
        email = EmailReceipt(
            sender="receipts@email.meijer.com",
            recipient="shopper@example.com",
            subject=None,
            body_html=html,
        )
        parser = MeijerEmailParser()
        result = parser.parse(email)
        assert result["purchase_date"] == "2026-04-01"

    def test_missing_totals_defaults_to_zero(self):
        html = "<html><body><p>Just an email with no totals</p></body></html>"
        email = EmailReceipt(
            sender="receipts@email.meijer.com",
            recipient="shopper@example.com",
            subject="Receipt",
            body_html=html,
        )
        parser = MeijerEmailParser()
        result = parser.parse(email)
        assert result["total"] == Decimal("0")
        assert result["subtotal"] is None
        assert result["tax"] is None
