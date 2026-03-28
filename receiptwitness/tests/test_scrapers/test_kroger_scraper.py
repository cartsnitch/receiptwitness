"""Tests for the Kroger scraper.

These tests mock Playwright to avoid requiring real Kroger credentials
or network access. They verify the scraper's control flow, session handling,
date filtering, and error resilience.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from receiptwitness.scrapers.base import RawReceipt, SessionData
from receiptwitness.scrapers.kroger import (
    DEFAULT_TIMEZONE,
    DEFAULT_USER_AGENT,
    DEFAULT_VIEWPORT,
    KROGER_BASE,
    KROGER_LOGIN_PAGE,
    KROGER_PURCHASE_HISTORY,
    KrogerScraper,
)


@pytest.fixture
def scraper():
    return KrogerScraper()


@pytest.fixture
def valid_session():
    return SessionData(
        cookies=[{"name": "session", "value": "abc123", "domain": ".kroger.com", "path": "/"}],
        user_agent=DEFAULT_USER_AGENT,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=2),
        extra={"retailer": "kroger"},
    )


@pytest.fixture
def expired_session():
    return SessionData(
        cookies=[{"name": "session", "value": "expired", "domain": ".kroger.com", "path": "/"}],
        user_agent=DEFAULT_USER_AGENT,
        created_at=datetime.now(UTC) - timedelta(hours=4),
        expires_at=datetime.now(UTC) - timedelta(hours=2),
    )


class TestKrogerScraperConstants:
    def test_base_url(self):
        assert KROGER_BASE == "https://www.kroger.com"

    def test_login_page(self):
        assert KROGER_LOGIN_PAGE == "https://www.kroger.com/signin"

    def test_purchase_history_page(self):
        assert KROGER_PURCHASE_HISTORY == "https://www.kroger.com/mypurchases"

    def test_default_user_agent_is_chrome(self):
        assert "Chrome" in DEFAULT_USER_AGENT
        assert "Windows" in DEFAULT_USER_AGENT

    def test_default_viewport_hd(self):
        assert DEFAULT_VIEWPORT == {"width": 1920, "height": 1080}

    def test_default_timezone(self):
        assert DEFAULT_TIMEZONE == "America/New_York"


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
        mock_page.url = "https://www.kroger.com/account/dashboard"
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

        with patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            result = await scraper.check_session(session)
            assert result is True

    @pytest.mark.asyncio
    async def test_session_redirected_to_signin_returns_false(self, scraper):
        session = SessionData(
            cookies=[],
            user_agent=DEFAULT_USER_AGENT,
            created_at=datetime.now(UTC),
            expires_at=None,
        )
        mock_page = AsyncMock()
        mock_page.url = "https://www.kroger.com/signin?redirectUrl=account"
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

        with patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw:
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
        mock_page.url = "https://www.kroger.com/"

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
                {"name": "kroger_session", "value": "test123", "domain": ".kroger.com", "path": "/"}
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            session = await scraper.login("user@test.com", "password123")

            assert isinstance(session, SessionData)
            assert len(session.cookies) == 1
            assert session.cookies[0]["name"] == "kroger_session"
            assert session.user_agent == DEFAULT_USER_AGENT
            assert session.expires_at is not None
            assert session.extra == {"retailer": "kroger"}


class TestScrapeReceipts:
    @pytest.mark.asyncio
    async def test_scrape_returns_receipts(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.status = 200
        mock_api_response.json = AsyncMock(
            return_value={
                "orders": [
                    {
                        "orderId": "KR-001",
                        "purchaseDate": "2026-03-10T14:00:00Z",
                        "storeNumber": "357",
                    },
                    {
                        "orderId": "KR-002",
                        "purchaseDate": "2026-03-11T10:00:00Z",
                        "storeNumber": "357",
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)

            assert len(receipts) == 2
            assert receipts[0].receipt_id == "KR-001"
            assert receipts[1].receipt_id == "KR-002"
            assert isinstance(receipts[0], RawReceipt)

    @pytest.mark.asyncio
    async def test_scrape_filters_by_date(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "orders": [
                    {
                        "orderId": "KR-OLD",
                        "purchaseDate": "2026-01-01T10:00:00Z",
                        "storeNumber": "357",
                    },
                    {
                        "orderId": "KR-NEW",
                        "purchaseDate": "2026-03-15T10:00:00Z",
                        "storeNumber": "357",
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session, since=since)

            assert len(receipts) == 1
            assert receipts[0].receipt_id == "KR-NEW"

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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
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
        """Kroger may use 'purchases' instead of 'orders'."""
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "purchases": [
                    {
                        "receiptId": "KR-ALT-001",
                        "transactionDate": "2026-03-10T14:00:00Z",
                        "divisionNumber": "014",
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)

            assert len(receipts) == 1
            assert receipts[0].receipt_id == "KR-ALT-001"

    @pytest.mark.asyncio
    async def test_scrape_skips_orders_without_id(self, scraper, valid_session):
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "orders": [
                    {"purchaseDate": "2026-03-10T14:00:00Z"},  # no id
                    {"orderId": "KR-VALID", "purchaseDate": "2026-03-10T14:00:00Z"},
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)
            assert len(receipts) == 1
            assert receipts[0].receipt_id == "KR-VALID"

    @pytest.mark.asyncio
    async def test_scrape_skips_orders_with_null_id(self, scraper, valid_session):
        """Ensure orderId: null doesn't produce receipt_id='None' (str(None) bug)."""
        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "orders": [
                    {"orderId": None, "receiptId": None, "purchaseDate": "2026-03-10T14:00:00Z"},
                    {"orderId": "KR-REAL", "purchaseDate": "2026-03-10T14:00:00Z"},
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
            patch("receiptwitness.scrapers.kroger.async_playwright") as mock_apw,
            patch.object(scraper, "human_delay", new_callable=AsyncMock),
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)
            assert len(receipts) == 1
            assert receipts[0].receipt_id == "KR-REAL"
            # Verify no receipt has the string "None" as its ID
            assert all(r.receipt_id != "None" for r in receipts)


class TestParseReceipt:
    def test_parse_receipt_delegates_to_parser(self, scraper):
        raw = RawReceipt(
            receipt_id="KR-001",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "TEST ITEM",
                            "basePrice": 5.00,
                            "totalPrice": 5.00,
                        }
                    ],
                    "total": 5.00,
                }
            },
        )
        result = scraper.parse_receipt(raw)
        assert result["receipt_id"] == "KR-001"
        assert len(result["items"]) == 1

    def test_receipt_detail_failure_returns_empty(self, scraper):
        """Verify receipt detail failures produce empty detail."""
        raw = RawReceipt(
            receipt_id="KR-FAIL",
            purchase_date="2026-03-12",
            raw_data={"total": 10.00, "detail": {}},
        )
        result = scraper.parse_receipt(raw)
        assert result["receipt_id"] == "KR-FAIL"
        assert result["items"] == []
