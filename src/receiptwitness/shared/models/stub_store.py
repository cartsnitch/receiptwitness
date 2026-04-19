"""Stub Store and StoreLocation models.

These are minimal stubs of the full cartsnitch-common Store/StoreLocation models.
They exist solely to satisfy SQLAlchemy relationship resolution for User and
UserStoreAccount. The canonical definitions live in cartsnitch/common.
"""

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from receiptwitness.shared.constants import StoreSlug
from receiptwitness.shared.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Store(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stub: canonical retailer. Full definition in cartsnitch/common."""

    __tablename__ = "stores"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[StoreSlug] = mapped_column(String(20), nullable=False, unique=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website_url: Mapped[str | None] = mapped_column(String(500))


class StoreLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stub: physical store location. Full definition in cartsnitch/common."""

    __tablename__ = "store_locations"

    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip: Mapped[str] = mapped_column(String(10), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
