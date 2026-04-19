"""ReceiptWitness ORM models — inlined from cartsnitch-common."""

from receiptwitness.shared.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from receiptwitness.shared.models.product import NormalizedProduct
from receiptwitness.shared.models.stub_purchase import Purchase, PurchaseItem

# Stub models — needed for relationship resolution but not directly used by receiptwitness.
# Full definitions live in cartsnitch/common.
from receiptwitness.shared.models.stub_store import Store, StoreLocation
from receiptwitness.shared.models.user import User, UserStoreAccount

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "NormalizedProduct",
    "Purchase",
    "PurchaseItem",
    "Store",
    "StoreLocation",
    "User",
    "UserStoreAccount",
]
