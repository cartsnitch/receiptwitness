"""Tests for the base scraper class."""

from datetime import datetime
from unittest.mock import patch

import pytest

from receiptwitness.scrapers.base import BaseScraper, RawReceipt, SessionData


class ConcreteScraper(BaseScraper):
    """Concrete implementation for testing the abstract base."""

    async def login(self, username, password):
        return SessionData(
            cookies=[],
            user_agent="test",
            created_at=datetime.now(),
        )

    async def check_session(self, session):
        return True

    async def scrape_receipts(self, session, since=None):
        return []

    def parse_receipt(self, raw):
        return {}


class TestBaseScraper:
    @pytest.mark.asyncio
    async def test_human_delay_respects_bounds(self):
        scraper = ConcreteScraper()
        with patch("receiptwitness.scrapers.base.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            await scraper.human_delay(min_ms=100, max_ms=200)
            call_args = mock_sleep.call_args[0][0]
            assert 0.1 <= call_args <= 0.2

    def test_raw_receipt_dataclass(self):
        receipt = RawReceipt(
            receipt_id="test-123",
            purchase_date="2026-03-10",
            store_number="42",
            raw_data={"key": "value"},
        )
        assert receipt.receipt_id == "test-123"
        assert receipt.raw_data == {"key": "value"}

    def test_session_data_defaults(self):
        session = SessionData(
            cookies=[],
            user_agent="test",
            created_at=datetime.now(),
        )
        assert session.expires_at is None
        assert session.extra == {}
