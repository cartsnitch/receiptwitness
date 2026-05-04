"""Shared test fixtures for pipeline tests."""

import secrets

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from receiptwitness.shared.models import Base
from receiptwitness.shared.models.user import User


@event.listens_for(User, "before_insert")
def _populate_email_inbound_token(mapper, connection, target):
    """Populate email_inbound_token with a secure random value when unset.

    SQLite has no gen_random_bytes() function, so we generate it in Python
    instead of relying on the PostgreSQL server_default.
    """
    if target.email_inbound_token is None:
        target.email_inbound_token = secrets.token_urlsafe(16)


@pytest.fixture
def engine():
    """In-memory SQLite engine for unit tests."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    """SQLAlchemy session bound to in-memory SQLite."""
    factory = sessionmaker(bind=engine)
    with factory() as sess:
        yield sess
