"""Tests for retailer detector."""

from receiptwitness.parsers.email.base import EmailReceipt
from receiptwitness.parsers.email.detector import detect_retailer


def test_detect_meijer():
    email = EmailReceipt(
        sender="receipts@meijer.com",
        recipient="user@example.com",
        subject="Your Receipt",
    )
    assert detect_retailer(email) == "meijer"


def test_detect_kroger():
    email = EmailReceipt(
        sender="noreply@email.kroger.com",
        recipient="user@example.com",
        subject="Your Receipt",
    )
    assert detect_retailer(email) == "kroger"


def test_detect_target():
    email = EmailReceipt(
        sender="Target <receipts@target.com>",
        recipient="user@example.com",
        subject="Your Receipt",
    )
    assert detect_retailer(email) == "target"


def test_detect_unknown():
    email = EmailReceipt(
        sender="noreply@walmart.com",
        recipient="user@example.com",
        subject="Your Receipt",
    )
    assert detect_retailer(email) is None


def test_detect_case_insensitive():
    email = EmailReceipt(
        sender="Receipts@MEIJER.COM",
        recipient="user@example.com",
        subject="Your Receipt",
    )
    assert detect_retailer(email) == "meijer"
