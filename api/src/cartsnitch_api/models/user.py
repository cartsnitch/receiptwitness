"""User and UserStoreAccount models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cartsnitch_api.constants import AccountStatus
from cartsnitch_api.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from cartsnitch_api.types import EncryptedJSON

if TYPE_CHECKING:
    from cartsnitch_api.models.purchase import Purchase
    from cartsnitch_api.models.store import Store


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Application user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    store_accounts: Mapped[list["UserStoreAccount"]] = relationship(back_populates="user")
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user")


class UserStoreAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Link between a user and their retailer account credentials."""

    __tablename__ = "user_store_accounts"
    __table_args__ = (UniqueConstraint("user_id", "store_id", name="uq_user_store_account"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    session_data: Mapped[dict | None] = mapped_column(EncryptedJSON)
    session_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[AccountStatus] = mapped_column(
        String(20), nullable=False, default=AccountStatus.ACTIVE
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="store_accounts")
    store: Mapped["Store"] = relationship(back_populates="user_accounts")
