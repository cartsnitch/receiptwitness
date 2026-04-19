"""Base interface for email receipt parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EmailReceipt:
    """Raw email data before parsing."""

    sender: str
    recipient: str
    subject: str
    body_html: str | None = None
    body_plain: str | None = None
    received_at: str | None = None
    raw_headers: dict = field(default_factory=dict)


class BaseEmailParser(ABC):
    """All retailer email parsers implement this interface."""

    @abstractmethod
    def can_parse(self, email: EmailReceipt) -> bool:
        """Return True if this parser handles this email."""
        ...

    @abstractmethod
    def parse(self, email: EmailReceipt) -> dict:
        """Parse email into a dict matching PurchaseCreate schema fields.
        Must include an items list matching PurchaseItemCreate fields."""
        ...
