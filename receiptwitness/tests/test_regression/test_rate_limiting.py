"""Regression tests: rate limiting and retry behavior.

Validates that scrapers enforce human-like delays between requests
and handle rate-limit/error responses gracefully without infinite retries.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from receiptwitness.scrapers.base import SessionData
from receiptwitness.scrapers.kroger import DEFAULT_USER_AGENT, KrogerScraper
from receiptwitness.scrapers.meijer import MeijerScraper


class TestHumanDelayBehavior:
    """Verify that human_delay respects configured bounds."""

    @pytest.mark.asyncio
    async def test_delay_within_bounds(self):
        """human_delay should sleep between min_ms/1000 and max_ms/1000 seconds."""
        scraper = KrogerScraper()
        sleep_path = "receiptwitness.scrapers.base.asyncio.sleep"
        with patch(sleep_path, new_callable=AsyncMock) as mock_sleep:
            await scraper.human_delay(100, 200)
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            assert 0.1 <= delay <= 0.2

    @pytest.mark.asyncio
    async def test_delay_uses_settings_defaults(self):
        """Without explicit args, should use settings.min/max_request_delay_ms."""
        scraper = MeijerScraper()
        sleep_path = "receiptwitness.scrapers.base.asyncio.sleep"
        with (
            patch("receiptwitness.scrapers.base.settings") as mock_settings,
            patch(sleep_path, new_callable=AsyncMock) as mock_sleep,
        ):
            mock_settings.min_request_delay_ms = 1000
            mock_settings.max_request_delay_ms = 5000
            await scraper.human_delay()
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            assert 1.0 <= delay <= 5.0

    @pytest.mark.asyncio
    async def test_delay_is_randomized(self):
        """Multiple calls should produce different delays (probabilistic)."""
        scraper = KrogerScraper()
        delays = []
        sleep_path2 = "receiptwitness.scrapers.base.asyncio.sleep"
        with patch(sleep_path2, new_callable=AsyncMock) as mock_sleep:
            for _ in range(20):
                await scraper.human_delay(100, 5000)
                delays.append(mock_sleep.call_args[0][0])
        # With range 100-5000ms, 20 calls should have at least 2 distinct values
        assert len(set(delays)) >= 2


class TestKrogerRateLimiting:
    """Verify Kroger scraper calls human_delay between receipt fetches."""

    @pytest.mark.asyncio
    async def test_delay_called_between_receipts(self):
        """Scraper must call human_delay for each receipt detail fetch."""
        scraper = KrogerScraper()
        valid_session = SessionData(
            cookies=[{"name": "s", "value": "v", "domain": ".kroger.com", "path": "/"}],
            user_agent=DEFAULT_USER_AGENT,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=2),
        )

        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "orders": [
                    {
                        "orderId": f"KR-{i}",
                        "purchaseDate": "2026-03-10T14:00:00Z",
                        "storeNumber": "357",
                    }
                    for i in range(3)
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = True
        mock_detail_response.json = AsyncMock(return_value={})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(side_effect=[mock_api_response] + [mock_detail_response] * 3)

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
            patch.object(scraper, "human_delay", new_callable=AsyncMock) as mock_delay,
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)

            assert len(receipts) == 3
            # human_delay called at least once per receipt (after initial page nav)
            # Plus once for the initial navigation delay
            assert mock_delay.call_count >= 3


class TestMeijerRateLimiting:
    """Verify Meijer scraper calls human_delay between receipt fetches."""

    @pytest.mark.asyncio
    async def test_delay_called_between_receipts(self):
        scraper = MeijerScraper()
        valid_session = SessionData(
            cookies=[{"name": "s", "value": "v", "domain": ".meijer.com", "path": "/"}],
            user_agent="test",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=4),
        )

        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "transactions": [
                    {
                        "transactionId": f"TXN-{i}",
                        "transactionDate": "2026-03-10T14:00:00Z",
                        "storeNumber": "42",
                    }
                    for i in range(3)
                ]
            }
        )

        mock_detail_response = AsyncMock()
        mock_detail_response.ok = True
        mock_detail_response.json = AsyncMock(return_value={})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(side_effect=[mock_api_response] + [mock_detail_response] * 3)

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
            patch.object(scraper, "human_delay", new_callable=AsyncMock) as mock_delay,
        ):
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_apw.return_value = mock_cm

            receipts = await scraper.scrape_receipts(valid_session)

            assert len(receipts) == 3
            assert mock_delay.call_count >= 3


class TestGracefulErrorRecovery:
    """Scrapers should not retry endlessly on errors."""

    @pytest.mark.asyncio
    async def test_kroger_api_500_returns_empty_not_retry(self):
        """500 error should return empty list, not retry."""
        scraper = KrogerScraper()
        valid_session = SessionData(
            cookies=[{"name": "s", "value": "v", "domain": ".kroger.com", "path": "/"}],
            user_agent=DEFAULT_USER_AGENT,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=2),
        )

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
            # Should only call the API once — no retries
            assert mock_request.get.call_count == 1

    @pytest.mark.asyncio
    async def test_kroger_429_returns_empty_not_retry(self):
        """Rate limit (429) should return empty, not retry."""
        scraper = KrogerScraper()
        valid_session = SessionData(
            cookies=[{"name": "s", "value": "v", "domain": ".kroger.com", "path": "/"}],
            user_agent=DEFAULT_USER_AGENT,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=2),
        )

        mock_api_response = AsyncMock()
        mock_api_response.ok = False
        mock_api_response.status = 429
        mock_api_response.status_text = "Too Many Requests"

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
            assert mock_request.get.call_count == 1

    @pytest.mark.asyncio
    async def test_meijer_detail_exception_continues(self):
        """Exception fetching one receipt detail should not abort remaining receipts."""
        scraper = MeijerScraper()
        valid_session = SessionData(
            cookies=[{"name": "s", "value": "v", "domain": ".meijer.com", "path": "/"}],
            user_agent="test",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=4),
        )

        mock_api_response = AsyncMock()
        mock_api_response.ok = True
        mock_api_response.json = AsyncMock(
            return_value={
                "transactions": [
                    {
                        "transactionId": "TXN-1",
                        "transactionDate": "2026-03-10T14:00:00Z",
                        "storeNumber": "42",
                    },
                    {
                        "transactionId": "TXN-2",
                        "transactionDate": "2026-03-11T10:00:00Z",
                        "storeNumber": "42",
                    },
                ]
            }
        )

        # First detail call raises exception, second succeeds
        mock_detail_fail = AsyncMock()
        mock_detail_fail.ok = False
        mock_detail_fail.status = 500

        mock_detail_ok = AsyncMock()
        mock_detail_ok.ok = True
        mock_detail_ok.json = AsyncMock(return_value={"items": []})

        mock_request = AsyncMock()
        mock_request.get = AsyncMock(
            side_effect=[mock_api_response, mock_detail_fail, mock_detail_ok]
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

            # Both receipts should be returned — the first with empty detail
            assert len(receipts) == 2
            assert receipts[0].raw_data.get("detail") == {}
            assert receipts[1].receipt_id == "TXN-2"
