"""Abstract base scraper interface for all retailer scrapers."""

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from receiptwitness.config import settings


@dataclass
class SessionData:
    """Holds session cookies and metadata for a retailer login."""

    cookies: list[dict]
    user_agent: str
    created_at: datetime
    expires_at: datetime | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class RawReceipt:
    """Raw receipt data before parsing."""

    receipt_id: str
    purchase_date: str
    store_number: str | None = None
    raw_data: dict = field(default_factory=dict)
    source_url: str | None = None


class BaseScraper(ABC):
    """All retailer scrapers implement this interface.

    Provides common functionality: human-like delays, rate limiting guards,
    and the abstract methods each retailer scraper must implement.
    """

    @abstractmethod
    async def login(self, username: str, password: str) -> SessionData:
        """Authenticate with the retailer portal and return session data."""
        ...

    @abstractmethod
    async def check_session(self, session: SessionData) -> bool:
        """Verify if an existing session is still valid."""
        ...

    @abstractmethod
    async def scrape_receipts(
        self, session: SessionData, since: datetime | None = None
    ) -> list[RawReceipt]:
        """Scrape receipt data from the retailer portal."""
        ...

    @abstractmethod
    def parse_receipt(self, raw: RawReceipt) -> dict:
        """Parse a raw receipt into structured data.

        Returns a dict with keys matching PurchaseCreate schema fields,
        including an 'items' list matching PurchaseItemCreate fields.
        """
        ...

    async def human_delay(self, min_ms: int | None = None, max_ms: int | None = None) -> None:
        """Sleep for a randomized human-like interval."""
        lo = min_ms or settings.min_request_delay_ms
        hi = max_ms or settings.max_request_delay_ms
        delay = random.randint(lo, hi) / 1000.0
        await asyncio.sleep(delay)
