"""Kroger loyalty portal scraper using Playwright.

Kroger uses Akamai Bot Manager for aggressive headless browser detection.
This scraper uses enhanced stealth measures including playwright-stealth,
realistic fingerprinting, and human-like interaction pacing.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import cast

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from receiptwitness.config import settings
from receiptwitness.scrapers.base import BaseScraper, RawReceipt, SessionData

logger = logging.getLogger(__name__)

# Kroger endpoints
KROGER_BASE = "https://www.kroger.com"
KROGER_LOGIN_PAGE = f"{KROGER_BASE}/signin"
KROGER_PURCHASE_HISTORY = f"{KROGER_BASE}/mypurchases"
KROGER_RECEIPT_API = f"{KROGER_BASE}/atlas/v1/purchase-history/api"
KROGER_RECEIPT_DETAIL_API = f"{KROGER_BASE}/atlas/v1/receipt/api"
KROGER_ACCOUNT_PAGE = f"{KROGER_BASE}/account/dashboard"

# Realistic browser fingerprint — Chrome on Windows (matches Kroger's typical audience)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
DEFAULT_LOCALE = "en-US"
DEFAULT_TIMEZONE = "America/New_York"


class KrogerScraper(BaseScraper):
    """Scraper for Kroger loyalty purchase history.

    Kroger uses Akamai Bot Manager which aggressively detects headless
    browsers. This scraper employs enhanced stealth measures:
    - Masks webdriver/automation signals
    - Sets realistic browser fingerprint
    - Uses human-like interaction pacing
    - Preserves browser context across sessions
    """

    async def _create_stealth_context(
        self, playwright_instance: Playwright, cookies: list[dict] | None = None
    ) -> BrowserContext:
        """Create a browser context with enhanced stealth for Akamai evasion."""
        browser = await playwright_instance.chromium.launch(
            headless=settings.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--window-size=1920,1080",
            ],
        )
        context = await browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport=DEFAULT_VIEWPORT,  # type: ignore[arg-type]
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
            java_script_enabled=True,
            bypass_csp=False,
            color_scheme="light",
            has_touch=False,
        )

        # Enhanced stealth script targeting Akamai Bot Manager detection vectors
        await context.add_init_script(
            """
            // Mask webdriver flag
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Chrome runtime object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: { isInstalled: false }
            };

            // Realistic plugin array
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });

            // Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });

            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });

            // Permissions query override (Akamai checks this)
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);

            // WebGL vendor/renderer (avoid "Google Inc." / "ANGLE" tells)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.call(this, parameter);
            };
            """
        )

        if cookies:
            await context.add_cookies(cookies)  # type: ignore[arg-type]

        return cast(BrowserContext, context)

    async def login(self, username: str, password: str) -> SessionData:
        """Log in to Kroger and capture session cookies."""
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
        """Execute the Kroger login flow."""
        logger.info("Navigating to Kroger sign-in page")
        await page.goto(KROGER_LOGIN_PAGE, wait_until="networkidle")
        await self.human_delay(2000, 4000)

        # Kroger login form — email/username field
        email_input = page.locator(
            'input[id="SignIn-emailInput"], '
            'input[name="email"], '
            'input[type="email"], '
            'input[data-testid="SignIn-emailInput"]'
        )
        await email_input.wait_for(state="visible", timeout=settings.browser_timeout_ms)
        await email_input.click()
        await self.human_delay(300, 700)
        await email_input.fill(username)
        await self.human_delay(800, 1500)

        # Password field
        password_input = page.locator(
            'input[id="SignIn-passwordInput"], '
            'input[name="password"], '
            'input[type="password"], '
            'input[data-testid="SignIn-passwordInput"]'
        )
        await password_input.wait_for(state="visible", timeout=settings.browser_timeout_ms)
        await password_input.click()
        await self.human_delay(300, 700)
        await password_input.fill(password)
        await self.human_delay(1000, 2000)

        # Sign-in button
        sign_in_btn = page.locator(
            'button[id="SignIn-submitButton"], '
            'button[data-testid="SignIn-submitButton"], '
            'button[type="submit"]:has-text("Sign In")'
        )
        await sign_in_btn.click()

        # Wait for redirect away from sign-in page
        await page.wait_for_url(
            lambda url: "signin" not in url.lower(),
            timeout=settings.browser_timeout_ms,
        )
        await self.human_delay(1500, 3000)

        # Capture cookies
        raw_cookies = await context.cookies()
        cookies = [dict(c) for c in raw_cookies]
        now = datetime.now(UTC)

        logger.info("Kroger login successful, captured %d cookies", len(cookies))
        return SessionData(
            cookies=cookies,
            user_agent=DEFAULT_USER_AGENT,
            created_at=now,
            expires_at=now + timedelta(hours=2),
            extra={"retailer": "kroger"},
        )

    async def check_session(self, session: SessionData) -> bool:
        """Check if the Kroger session is still valid."""
        if session.expires_at and datetime.now(UTC) > session.expires_at:
            logger.info("Kroger session expired based on timestamp")
            return False

        async with async_playwright() as p:
            context = await self._create_stealth_context(p, cookies=session.cookies)
            page = await context.new_page()
            try:
                response = await page.goto(KROGER_ACCOUNT_PAGE, wait_until="networkidle")
                current_url = page.url.lower()
                is_valid = "signin" not in current_url and response is not None and response.ok
                logger.info("Kroger session check: valid=%s (url=%s)", is_valid, page.url)
                return is_valid
            except Exception:
                logger.exception("Kroger session check failed")
                return False
            finally:
                if context.browser:
                    await context.browser.close()

    async def scrape_receipts(
        self, session: SessionData, since: datetime | None = None
    ) -> list[RawReceipt]:
        """Scrape purchase history from Kroger."""
        async with async_playwright() as p:
            context = await self._create_stealth_context(p, cookies=session.cookies)
            page = await context.new_page()
            try:
                return await self._fetch_receipts(page, since)
            finally:
                if context.browser:
                    await context.browser.close()

    async def _fetch_receipts(self, page: Page, since: datetime | None) -> list[RawReceipt]:
        """Fetch receipt list and details from Kroger purchase history."""
        # Navigate to purchase history to establish context
        await page.goto(KROGER_PURCHASE_HISTORY, wait_until="networkidle")
        await self.human_delay(1500, 3000)

        receipts: list[RawReceipt] = []

        # Kroger purchase history API endpoint
        api_response = await page.request.get(KROGER_RECEIPT_API)
        if not api_response.ok:
            logger.warning(
                "Kroger purchase history request failed: %d %s",
                api_response.status,
                api_response.status_text,
            )
            return []

        response = await api_response.json()
        if not isinstance(response, dict):
            logger.warning("Unexpected purchase history response type: %s", type(response))
            return []

        # Handle Kroger's response structure
        orders = response.get("orders", response.get("purchases", []))
        if not isinstance(orders, list):
            logger.warning("No orders found in Kroger purchase history response")
            return []

        logger.info("Found %d orders in Kroger purchase history", len(orders))

        for order in orders:
            raw_id = order.get("orderId") or order.get("receiptId") or order.get("id") or ""
            order_id = str(raw_id)
            purchase_date = order.get(
                "purchaseDate", order.get("transactionDate", order.get("date", ""))
            )

            # Filter by date if 'since' is provided
            if since and purchase_date:
                try:
                    txn_dt = datetime.fromisoformat(purchase_date.replace("Z", "+00:00"))
                    if txn_dt < since:
                        continue
                except (ValueError, TypeError):
                    pass

            if not order_id:
                continue

            await self.human_delay(1000, 2500)

            # Fetch receipt detail
            detail = await self._fetch_receipt_detail(page, order_id)

            raw_store = (
                order.get("storeNumber")
                or order.get("divisionNumber")
                or order.get("storeId")
                or ""
            )
            store_number = str(raw_store)

            receipts.append(
                RawReceipt(
                    receipt_id=order_id,
                    purchase_date=purchase_date,
                    store_number=store_number,
                    raw_data={**order, "detail": detail},
                    source_url=f"{KROGER_RECEIPT_DETAIL_API}?orderId={order_id}",
                )
            )

        logger.info("Scraped %d receipts from Kroger", len(receipts))
        return receipts

    async def _fetch_receipt_detail(self, page: Page, order_id: str) -> dict:
        """Fetch detailed receipt data for a single Kroger order."""
        try:
            url = f"{KROGER_RECEIPT_DETAIL_API}?orderId={order_id}"
            api_response = await page.request.get(url)
            if not api_response.ok:
                logger.warning(
                    "Kroger receipt detail request failed for %s: %d",
                    order_id,
                    api_response.status,
                )
                return {}
            detail = await api_response.json()
            return detail if isinstance(detail, dict) else {}
        except Exception:
            logger.exception("Failed to fetch Kroger receipt detail for %s", order_id)
            return {}

    def parse_receipt(self, raw: RawReceipt) -> dict:
        """Parse raw Kroger receipt into structured purchase data."""
        from receiptwitness.parsers.kroger import parse_kroger_receipt

        return parse_kroger_receipt(raw)
