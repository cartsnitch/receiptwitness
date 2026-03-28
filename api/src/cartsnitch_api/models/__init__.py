"""SQLAlchemy ORM models — re-exports all models for convenience."""

from cartsnitch_api.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from cartsnitch_api.models.coupon import Coupon
from cartsnitch_api.models.price import PriceHistory
from cartsnitch_api.models.product import NormalizedProduct
from cartsnitch_api.models.purchase import Purchase, PurchaseItem
from cartsnitch_api.models.shrinkflation import ShrinkflationEvent
from cartsnitch_api.models.store import Store, StoreLocation
from cartsnitch_api.models.user import User, UserStoreAccount

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "Store",
    "StoreLocation",
    "User",
    "UserStoreAccount",
    "Purchase",
    "PurchaseItem",
    "NormalizedProduct",
    "PriceHistory",
    "Coupon",
    "ShrinkflationEvent",
]
