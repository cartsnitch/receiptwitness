"""Tests for the Meijer scraper.

These tests mock Playwright to avoid requiring real Meijer credentials
or network access. They verify the scraper's control flow, session handling,
date filtering, and error resilience.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from receiptwitness.scrapers.base import RawReceipt, SessionData
from receiptwitness.scrapers.meijer import (
    DEFAULT_TIMEZONE,
    DEFAULT_USER_AGENT,
    DEFAULT_VIEWPORT,
    MEIJER_BASE,
    MEIJER_LOGIN_PAGE,
    MEIJER_MPERKS_HOME,
    MEIJER_PURCHASE_HISTORY,
    MeijerScraper,
)


@pytest.fixture
def scraper():
    return MeijerScraper()


@pytest.fixture
def valid_session():
    return SessionData(
        cookies=[
            {"name": "meijer_session", "value": "abc123", "domain": ".meijer.com", "path": "/"}
        ],
        user_agent=DEFAULT_USER_AGENT,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=4),
    )


@pytest.fixture
def expired_session():
    return SessionData(
        cookies=[
            {"name": "meijer_session", "value": "expired", "domain": ".meijer.com", "path": "/"}
        ],
        user_agent=DEFAULT_USER_AGENT,
        created_at=datetime.now(UTC) - timedelta(hours=8),
        expires_at=datetime.now(UTC) - timedelta(hours=4),
    )


class TestMeijerScraperConstants:
    def test_base_url(self):
        assert MEIJER_BASE == "https://www.meijer.com"

    def test_login_page(self):
        assert MEIJER_LOGIN_PAGE == "https://www.meijer.com/shopping/login.html"

    def test_mperks_home(self):
        assert MEIJER_MPERKS_HOME == "https://www.meijer.com/mperks.html"

    def test_purchase_history_url(self):
        assert (
            MEIJER_PURCHASE_HISTORY == "https://www.meijer.com/bin/meijer/profile/purchasehistory"
        )

    def test_default_user_agent_is_chrome(self):
        assert "Chrome" in DEFAULT_USER_AGENT
        assert "Windows" in DEFAULT_USER_AGENT

    def test_default_viewport_hd(self):
        assert DEFAULT_VIEWPORT == {"width": 1920, "height": 1080}

    def test_default_timezone(self):
        assert DEFAULT_TIMEZONE == "America/Detroit"


class TestCheckSession:
    @pytest.mark.asyncio
    async def test_expired_session_returns_false(self, scraper, expired_session):
        result = await scraper.check_session(expired_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_no_expiry_checks_via_browser(self, scraper):
        session = SessionData(
            cookies=[],
            user_agent=DEFAULT_USER_AGENT,
            created_at=datetime.now(UTC),
            expires_at=None,
        )
        mock_page = AsyncMock()
        mock_page.url = "https://www.meijer.com/mperks.html"
        mock_response = MagicMock()
        mock_response.ok = True
        mock_page.goto = AsyncMock(return_value=mock_response)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            result = await scraper.check_session(session)
            assert result is True

    @pytest.mark.asyncio
    async def test_session_redirected_to_login_returns_false(self, scraper):
        session = SessionData(
            cookies=[],
            user_agent=DEFAULT_USER_AGENT,
            created_at=datetime.now(UTC),
            expires_at=None,
        )
        mock_page = AsyncMock()
        mock_page.url = "https://www.meijer.com/shopping/login.html?redirect=mperks"
        mock_response = MagicMock()
        mock_response.ok = True
        mock_page.goto = AsyncMock(return_value=mock_response)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            result = await scraper.check_session(session)
            assert result is False


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_returns_session_data(self, scraper):
        mock_page = AsyncMock()
        mock_page.url = "https://www.meijer.com/mperks.html"

        # Mock locator chain
        mock_email = AsyncMock()
        mock_password = AsyncMock()
        mock_button = AsyncMock()
        mock_page.locator = MagicMock(side_effect=[mock_email, mock_password, mock_button])
        mock_page.wait_for_url = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.cookies = AsyncMock(
            return_value=[
                {"name": "meijer_session", "value": "test456", "domain": ".meijer.com", "path": "/"}
            ]
        )
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            session = await scraper.login("user@test.com", "password123")

            assert isinstance(session, SessionData)
            assert len(session.cookies) == 1
            assert session.cookies[0]["name"] == "meijer_session"
            assert session.user_agent == DEFAULT_USER_AGENT
            assert session.expires_at is not None
            # Meijer sessions last 4 hours
            assert session.expires_at > session.created_at + timedelta(hours=3)


class TestScrapeReceipts:
    @pytest.mark.asyncio
    async def test_scrape_returns_receipts(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.status = 200
        mock_api_response.json = AsyncMock(
            return_value={
                "transactions": [
                    {
                        "transactionId": "TXN-001",
                        "transactionDate": "2026-03-10T14:00:00Z",
                        "storeNumber": "42",
                    },
                    {
                        "transactionId": "TXN-002",
                        "transactionDate": "2026-03-11T10:00:00Z",
                        "storeNumber": "42",
                    },
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = True
        mock_detail_response.json = AsyncMock(return_value={"items": []})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(
            side_effect=[mock_api_response, mock_detail_response, mock_detail_response]
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)

            assert len(receipts) == 2
            assert receipts[0].receipt_id == "TXN-001"
            assert receipts[1].receipt_id == "TXN-002"
            assert isinstance(receipts[0], RawReceipt)

    @pytest.mark.asyncio
    async def test_scrape_filters_by_date(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "transactions": [
                    {
                        "transactionId": "TXN-OLD",
                        "transactionDate": "2026-01-01T10:00:00Z",
                        "storeNumber": "42",
                    },
                    {
                        "transactionId": "TXN-NEW",
                        "transactionDate": "2026-03-15T10:00:00Z",
                        "storeNumber": "42",
                    },
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = True
        mock_detail_response.json = AsyncMock(return_value={})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(side_effect=[mock_api_response, mock_detail_response])

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        since = datetime(2026, 3, 1, tzinfo=UTC)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session, since=since)

            assert len(receipts) == 1
            assert receipts[0].receipt_id == "TXN-NEW"

    @pytest.mark.asyncio
    async def test_scrape_handles_api_failure(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = False
        mock_api_response.status = 500
        mock_api_response.status_text = "Internal Server Error"

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(return_value=mock_api_response)

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)
            assert receipts == []

    @pytest.mark.asyncio
    async def test_scrape_handles_unexpected_response(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(return_value="not a dict")

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(return_value=mock_api_response)

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)
            assert receipts == []

    @pytest.mark.asyncio
    async def test_scrape_alternative_field_names(self, scraper, valid_session):
        """Meijer may use 'purchaseHistory' instead of 'transactions'."""
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "purchaseHistory": [
                    {
                        "receiptId": "MJ-ALT-001",
                        "purchaseDate": "2026-03-10T14:00:00Z",
                        "storeId": "99",
                    }
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = True
        mock_detail_response.json = AsyncMock(return_value={})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(side_effect=[mock_api_response, mock_detail_response])

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)

            assert len(receipts) == 1
            assert receipts[0].receipt_id == "MJ-ALT-001"

    @pytest.mark.asyncio
    async def test_scrape_skips_transactions_without_id(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "transactions": [
                    {"transactionDate": "2026-03-10T14:00:00Z"},  # no id
                    {"transactionId": "TXN-VALID", "transactionDate": "2026-03-10T14:00:00Z"},
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = True
        mock_detail_response.json = AsyncMock(return_value={})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(side_effect=[mock_api_response, mock_detail_response])

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)
            assert len(receipts) == 1
            assert receipts[0].receipt_id == "TXN-VALID"

    @pytest.mark.asyncio
    async def test_scrape_receipt_detail_failure_returns_empty_detail(self, scraper, valid_session):
        """Receipt detail API failure should not crash the scraper."""
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "transactions": [
                    {
                        "transactionId": "TXN-DETAIL-FAIL",
                        "transactionDate": "2026-03-10T14:00:00Z",
                        "storeNumber": "42",
                    }
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = False
        mock_detail_response.status = 404

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(side_effect=[mock_api_response, mock_detail_response])

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.request = mock_request

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.browser = mock_browser

        mock_pw = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with (
            patch("receiptwitness.scrapers.meijer.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)
            assert len(receipts) == 1
            assert receipts[0].receipt_id == "TXN-DETAIL-FAIL"
            assert receipts[0].raw_data.get("detail") == {}


class TestParseReceipt:
    def test_parse_receipt_delegates_to_parser(self, scraper):
        raw = RawReceipt(
            receipt_id="TXN-001",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "TEST ITEM",
                            "price": 5.00,
                            "extendedPrice": 5.00,
                        }
                    ],
                    "total": 5.00,
                }
            },
        )
        result = scraper.parse_receipt(raw)
        assert result["receipt_id"] == "TXN-001"
        assert len(result["items"]) == 1

    def test_receipt_detail_failure_returns_empty(self, scraper):
        raw = RawReceipt(
            receipt_id="TXN-FAIL",
            purchase_date="2026-03-10",
            raw_data={"total": 10.00, "detail": {}},
        )
        result = scraper.parse_receipt(raw)
        assert result["receipt_id"] == "TXN-FAIL"
        assert result["items"] == []
