"""Target Circle scraper using Playwright.

Target stores ~1 year of in-store purchase history tied to Circle accounts.
Purchases appear when the user pays with a linked card, uses the Target app
wallet, or enters their Circle phone number at checkout.

Key endpoints (reverse-engineered from target.com SPA):
- Login:          POST https://gsp.target.com/gsp/authentications/v1/auth_codes
- Order history:  GET  https://api.target.com/order_history/v1/orders (in-store tab)
- Receipt detail: GET  https://api.target.com/order_history/v1/orders/{orderId}
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import cast

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from receiptwitness.config import settings
from receiptwitness.scrapers.base import BaseScraper, RawReceipt, SessionData

logger = logging.getLogger(__name__)

# Target endpoints
TARGET_BASE = "https://www.target.com"
TARGET_LOGIN_PAGE = f"{TARGET_BASE}/login"
TARGET_ACCOUNT_PAGE = f"{TARGET_BASE}/account"
TARGET_ORDER_HISTORY = f"{TARGET_BASE}/account/orders"
TARGET_ORDER_API = "https://api.target.com/order_history/v1/orders"
TARGET_RECEIPT_API = "https://api.target.com/order_history/v1/orders"

# Realistic browser fingerprint — Chrome on Windows
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
DEFAULT_LOCALE = "en-US"
DEFAULT_TIMEZONE = "America/Detroit"  # SE Michigan coverage


class TargetScraper(BaseScraper):
    """Scraper for Target Circle in-store purchase history.

    Target's order history SPA loads purchase data from internal API
    endpoints. This scraper authenticates via the web login flow,
    captures session cookies, and uses those to hit the order history
    API for in-store receipt data.
    """

    async def _create_stealth_context(
        self, playwright_instance: Playwright, cookies: list[dict] | None = None
    ) -> BrowserContext:
        """Create a browser context with stealth settings for Target."""
        browser = await playwright_instance.chromium.launch(
            headless=settings.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
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
        # Mask webdriver and automation signals
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: { isInstalled: false }
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });

            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });

            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            """
        )
        if cookies:
            await context.add_cookies(cookies)  # type: ignore[arg-type]
        return cast(BrowserContext, context)

    async def login(self, username: str, password: str) -> SessionData:
        """Log in to Target and capture session cookies."""
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
        """Execute the Target login flow."""
        logger.info("Navigating to Target sign-in page")
        await page.goto(TARGET_LOGIN_PAGE, wait_until="networkidle")
        await self.human_delay(2000, 4000)

        # Target login form — email/username field
        email_input = page.locator(
            'input[id="username"], '
            'input[name="username"], '
            'input[type="email"], '
            'input[data-test="username"]'
        )
        await email_input.wait_for(state="visible", timeout=settings.browser_timeout_ms)
        await email_input.click()
        await self.human_delay(300, 700)
        await email_input.fill(username)
        await self.human_delay(800, 1500)

        # Password field
        password_input = page.locator(
            'input[id="password"], '
            'input[name="password"], '
            'input[type="password"], '
            'input[data-test="password"]'
        )
        await password_input.wait_for(state="visible", timeout=settings.browser_timeout_ms)
        await password_input.click()
        await self.human_delay(300, 700)
        await password_input.fill(password)
        await self.human_delay(1000, 2000)

        # Sign-in button
        sign_in_btn = page.locator(
            'button[id="login"], '
            'button[data-test="login-button"], '
            'button[type="submit"]:has-text("Sign in")'
        )
        await sign_in_btn.click()

        # Wait for redirect away from login page
        await page.wait_for_url(
            lambda url: "login" not in url.lower(),
            timeout=settings.browser_timeout_ms,
        )
        await self.human_delay(1500, 3000)

        # Capture cookies
        raw_cookies = await context.cookies()
        cookies = [dict(c) for c in raw_cookies]
        now = datetime.now(UTC)

        logger.info("Target login successful, captured %d cookies", len(cookies))
        return SessionData(
            cookies=cookies,
            user_agent=DEFAULT_USER_AGENT,
            created_at=now,
            expires_at=now + timedelta(hours=2),
            extra={"retailer": "target"},
        )

    async def check_session(self, session: SessionData) -> bool:
        """Check if the Target session is still valid."""
        if session.expires_at and datetime.now(UTC) > session.expires_at:
            logger.info("Target session expired based on timestamp")
            return False

        async with async_playwright() as p:
            context = await self._create_stealth_context(p, cookies=session.cookies)
            page = await context.new_page()
            try:
                response = await page.goto(TARGET_ACCOUNT_PAGE, wait_until="networkidle")
                current_url = page.url.lower()
                is_valid = "login" not in current_url and response is not None and response.ok
                logger.info("Target session check: valid=%s (url=%s)", is_valid, page.url)
                return is_valid
            except Exception:
                logger.exception("Target session check failed")
                return False
            finally:
                if context.browser:
                    await context.browser.close()

    async def scrape_receipts(
        self, session: SessionData, since: datetime | None = None
    ) -> list[RawReceipt]:
        """Scrape in-store purchase history from Target Circle."""
        async with async_playwright() as p:
            context = await self._create_stealth_context(p, cookies=session.cookies)
            page = await context.new_page()
            try:
                return await self._fetch_receipts(page, since)
            finally:
                if context.browser:
                    await context.browser.close()

    async def _fetch_receipts(self, page: Page, since: datetime | None) -> list[RawReceipt]:
        """Fetch receipt list and details from Target order history.

        Target's order history page has separate tabs for online and in-store
        purchases. We target the in-store tab which shows Circle-linked
        transactions.
        """
        # Navigate to order history to establish context
        await page.goto(TARGET_ORDER_HISTORY, wait_until="networkidle")
        await self.human_delay(1500, 3000)

        receipts: list[RawReceipt] = []

        # Target order history API — filter for in-store purchases
        api_response = await page.request.get(
            TARGET_ORDER_API,
            params={"channel": "in_store", "limit": "50"},
        )
        if not api_response.ok:
            logger.warning(
                "Target order history request failed: %d %s",
                api_response.status,
                api_response.status_text,
            )
            return []

        response = await api_response.json()
        if not isinstance(response, dict):
            logger.warning("Unexpected order history response type: %s", type(response))
            return []

        # Target uses "orders" key for in-store purchase list
        orders = response.get("orders", response.get("transactions", []))
        if not isinstance(orders, list):
            logger.warning("No orders found in Target order history response")
            return []

        logger.info("Found %d in-store orders in Target history", len(orders))

        for order in orders:
            raw_id = order.get("orderId") or order.get("transactionId") or order.get("id") or ""
            order_id = str(raw_id)
            purchase_date = order.get(
                "purchaseDate",
                order.get("transactionDate", order.get("date", "")),
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
                order.get("storeNumber") or order.get("storeId") or order.get("locationId") or ""
            )
            store_number = str(raw_store)

            receipts.append(
                RawReceipt(
                    receipt_id=order_id,
                    purchase_date=purchase_date,
                    store_number=store_number,
                    raw_data={**order, "detail": detail},
                    source_url=f"{TARGET_RECEIPT_API}/{order_id}",
                )
            )

        logger.info("Scraped %d receipts from Target", len(receipts))
        return receipts

    async def _fetch_receipt_detail(self, page: Page, order_id: str) -> dict:
        """Fetch detailed receipt data for a single Target order."""
        try:
            url = f"{TARGET_RECEIPT_API}/{order_id}"
            api_response = await page.request.get(url)
            if not api_response.ok:
                logger.warning(
                    "Target receipt detail request failed for %s: %d",
                    order_id,
                    api_response.status,
                )
                return {}
            detail = await api_response.json()
            return detail if isinstance(detail, dict) else {}
        except Exception:
            logger.exception("Failed to fetch Target receipt detail for %s", order_id)
            return {}

    def parse_receipt(self, raw: RawReceipt) -> dict:
        """Parse raw Target receipt into structured purchase data."""
        from receiptwitness.parsers.target import parse_target_receipt

        return parse_target_receipt(raw)
