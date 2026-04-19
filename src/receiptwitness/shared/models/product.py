"""NormalizedProduct model — the canonical product identity."""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from receiptwitness.shared.constants import ProductCategory, SizeUnit
from receiptwitness.shared.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    pass


class NormalizedProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical product identity — matches products across retailers."""

    __tablename__ = "normalized_products"

    canonical_name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[ProductCategory | None] = mapped_column(String(50))
    subcategory: Mapped[str | None] = mapped_column(String(100))
    brand: Mapped[str | None] = mapped_column(String(200))
    size: Mapped[str | None] = mapped_column(String(50))
    size_unit: Mapped[SizeUnit | None] = mapped_column(String(10))
    upc_variants: Mapped[list[str] | None] = mapped_column(JSON, default=list)
