"""Meijer mPerks scraper using Playwright.

Meijer has no public API. We reverse-engineer the XHR endpoints the mPerks
web app uses to pull purchase history and receipt data. The flow:

1. Launch stealth Playwright browser
2. Navigate to mPerks login page and authenticate
3. Capture session cookies after successful login
4. Use those cookies to hit the mPerks receipt API endpoints directly
5. Parse receipt JSON into structured PurchaseCreate records

Key endpoints (reverse-engineered from mPerks SPA):
- Login:       POST https://www.meijer.com/bin/meijer/account/login
- Receipts:    GET  https://www.meijer.com/bin/meijer/profile/purchasehistory
- Receipt detail: GET https://www.meijer.com/bin/meijer/profile/receipt?receiptId=...
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import cast

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from receiptwitness.config import settings
from receiptwitness.scrapers.base import BaseScraper, RawReceipt, SessionData

logger = logging.getLogger(__name__)

# Meijer mPerks URLs
MEIJER_BASE = "https://www.meijer.com"
MEIJER_LOGIN_PAGE = f"{MEIJER_BASE}/shopping/login.html"
MEIJER_LOGIN_API = f"{MEIJER_BASE}/bin/meijer/account/login"
MEIJER_PURCHASE_HISTORY = f"{MEIJER_BASE}/bin/meijer/profile/purchasehistory"
MEIJER_RECEIPT_DETAIL = f"{MEIJER_BASE}/bin/meijer/profile/receipt"
MEIJER_MPERKS_HOME = f"{MEIJER_BASE}/mperks.html"

# Realistic browser fingerprint
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
DEFAULT_LOCALE = "en-US"
DEFAULT_TIMEZONE = "America/Detroit"  # Meijer HQ is in Grand Rapids, MI


class MeijerScraper(BaseScraper):
    """Scraper for Meijer mPerks purchase history."""

    async def _create_stealth_context(
        self, playwright_instance: Playwright, cookies: list[dict] | None = None
    ) -> BrowserContext:
        """Create a browser context with stealth settings."""
        browser = await playwright_instance.chromium.launch(
            headless=settings.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = await browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport=DEFAULT_VIEWPORT,  # type: ignore[arg-type]
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
            java_script_enabled=True,
            bypass_csp=False,
        )
        # Mask webdriver flag
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            // Mask chrome automation indicators
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            """
        )
        if cookies:
            await context.add_cookies(cookies)  # type: ignore[arg-type]
        return cast(BrowserContext, context)

    async def login(self, username: str, password: str) -> SessionData:
        """Log in to Meijer mPerks and capture session cookies.

        The mPerks login flow:
        1. Navigate to login page
        2. Fill email and password fields
        3. Click sign-in button
        4. Wait for redirect to mPerks dashboard
        5. Extract session cookies
        """
        async with async_playwright() as p:
            context = await self._create_stealth_context(p)
            page = await context.new_page()
            try:
                return await self._perform_login(page, context, username, password)
            finally:
                if context.browser:
                    await context.browser.close()

    async def _perform_login(
        self, page: Page, context: BrowserContext, username: str, password: str
    ) -> SessionData:
        """Execute the login flow on the mPerks portal."""
        logger.info("Navigating to Meijer login page")
        await page.goto(MEIJER_LOGIN_PAGE, wait_until="networkidle")
        await self.human_delay(1500, 3000)

        # Fill email field
        email_input = page.locator('input[type="email"], input[name="email"], #email')
        await email_input.wait_for(state="visible", timeout=settings.browser_timeout_ms)
        await email_input.click()
        await self.human_delay(200, 500)
        await email_input.fill(username)
        await self.human_delay(500, 1000)

        # Fill password field
        password_input = page.locator('input[type="password"], input[name="password"], #password')
        await password_input.wait_for(state="visible", timeout=settings.browser_timeout_ms)
        await password_input.click()
        await self.human_delay(200, 500)
        await password_input.fill(password)
        await self.human_delay(500, 1500)

        # Click sign-in button
        sign_in_btn = page.locator(
            'button[type="submit"], button:has-text("Sign In"), button:has-text("Log In")'
        )
        await sign_in_btn.click()

        # Wait for navigation after login
        await page.wait_for_url(
            lambda url: "login" not in url.lower(),
            timeout=settings.browser_timeout_ms,
        )
        await self.human_delay(1000, 2000)

        # Capture cookies
        raw_cookies = await context.cookies()
        cookies = [dict(c) for c in raw_cookies]
        now = datetime.now(UTC)

        logger.info("Meijer login successful, captured %d cookies", len(cookies))
        return SessionData(
            cookies=cookies,
            user_agent=DEFAULT_USER_AGENT,
            created_at=now,
            expires_at=now + timedelta(hours=4),
        )

    async def check_session(self, session: SessionData) -> bool:
        """Check if the mPerks session is still valid.

        Makes a lightweight request to the mPerks home page and checks
        if we get redirected to login (session expired) or not.
        """
        if session.expires_at and datetime.now(UTC) > session.expires_at:
            logger.info("Meijer session expired based on timestamp")
            return False

        async with async_playwright() as p:
            context = await self._create_stealth_context(p, cookies=session.cookies)
            page = await context.new_page()
            try:
                response = await page.goto(MEIJER_MPERKS_HOME, wait_until="networkidle")
                current_url = page.url.lower()
                is_valid = "login" not in current_url and response is not None and response.ok
                logger.info("Meijer session check: valid=%s (url=%s)", is_valid, page.url)
                return is_valid
            except Exception:
                logger.exception("Meijer session check failed")
                return False
            finally:
                if context.browser:
                    await context.browser.close()

    async def scrape_receipts(
        self, session: SessionData, since: datetime | None = None
    ) -> list[RawReceipt]:
        """Scrape purchase history from Meijer mPerks.

        Uses the XHR endpoints the mPerks SPA calls to fetch receipt data.
        The purchase history endpoint returns a list of recent transactions,
        and we can fetch individual receipt details for line items.
        """
        async with async_playwright() as p:
            context = await self._create_stealth_context(p, cookies=session.cookies)
            page = await context.new_page()
            try:
                return await self._fetch_receipts(page, since)
            finally:
                if context.browser:
                    await context.browser.close()

    async def _fetch_receipts(self, page: Page, since: datetime | None) -> list[RawReceipt]:
        """Fetch receipt list and detail via mPerks XHR endpoints.

        Uses Playwright's page.request API (APIRequestContext) instead of
        page.evaluate(fetch(...)) for better observability — requests show up
        in Playwright traces and can be intercepted by route handlers.
        """
        # Navigate to mPerks to establish context (cookies need domain context)
        await page.goto(MEIJER_MPERKS_HOME, wait_until="networkidle")
        await self.human_delay(1000, 2000)

        receipts: list[RawReceipt] = []

        # Fetch purchase history listing via page.request (APIRequestContext)
        api_response = await page.request.get(MEIJER_PURCHASE_HISTORY)
        if not api_response.ok:
            logger.warning(
                "Purchase history request failed: %d %s",
                api_response.status,
                api_response.status_text,
            )
            return []

        response = await api_response.json()

        if not isinstance(response, dict):
            logger.warning("Unexpected purchase history response type: %s", type(response))
            return []

        transactions = response.get("transactions", response.get("purchaseHistory", []))
        if not isinstance(transactions, list):
            logger.warning("No transactions found in purchase history response")
            return []

        logger.info("Found %d transactions in Meijer purchase history", len(transactions))

        for txn in transactions:
            receipt_id = str(txn.get("transactionId", txn.get("receiptId", "")))
            purchase_date = txn.get("transactionDate", txn.get("purchaseDate", ""))

            # Filter by date if 'since' is provided
            if since and purchase_date:
                try:
                    txn_dt = datetime.fromisoformat(purchase_date.replace("Z", "+00:00"))
                    if txn_dt < since:
                        continue
                except (ValueError, TypeError):
                    pass

            if not receipt_id:
                continue

            await self.human_delay(800, 2000)

            # Fetch receipt detail
            detail = await self._fetch_receipt_detail(page, receipt_id)

            receipts.append(
                RawReceipt(
                    receipt_id=receipt_id,
                    purchase_date=purchase_date,
                    store_number=str(txn.get("storeNumber", txn.get("storeId", ""))),
                    raw_data={**txn, "detail": detail},
                    source_url=f"{MEIJER_RECEIPT_DETAIL}?receiptId={receipt_id}",
                )
            )

        logger.info("Scraped %d receipts from Meijer", len(receipts))
        return receipts

    async def _fetch_receipt_detail(self, page: Page, receipt_id: str) -> dict:
        """Fetch detailed receipt data for a single transaction.

        Uses Playwright's page.request API for traceability.
        """
        try:
            url = f"{MEIJER_RECEIPT_DETAIL}?receiptId={receipt_id}"
            api_response = await page.request.get(url)
            if not api_response.ok:
                logger.warning(
                    "Receipt detail request failed for %s: %d",
                    receipt_id,
                    api_response.status,
                )
                return {}
            detail = await api_response.json()
            return detail if isinstance(detail, dict) else {}
        except Exception:
            logger.exception("Failed to fetch receipt detail for %s", receipt_id)
            return {}

    def parse_receipt(self, raw: RawReceipt) -> dict:
        """Parse raw Meijer receipt into structured purchase data.

        Delegates to the dedicated parser module.
        """
        from receiptwitness.parsers.meijer import parse_meijer_receipt

        return parse_meijer_receipt(raw)
