"""Tests for session manager logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet

from receiptwitness.scrapers.base import SessionData
from receiptwitness.session.manager import (
    get_valid_session,
    session_from_db_record,
    session_to_db_value,
)

TEST_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _mock_encryption_key():
    with patch("receiptwitness.session.encryption.settings") as mock_settings:
        mock_settings.session_encryption_key = TEST_KEY
        yield


def _make_session(hours_until_expire: int = 4) -> SessionData:
    now = datetime.now(UTC)
    return SessionData(
        cookies=[{"name": "sid", "value": "test", "domain": ".meijer.com"}],
        user_agent="Mozilla/5.0",
        created_at=now,
        expires_at=now + timedelta(hours=hours_until_expire),
    )


class TestSessionSerialization:
    def test_roundtrip(self):
        session = _make_session()
        db_value = session_to_db_value(session)
        restored = session_from_db_record(db_value)

        assert restored is not None
        assert restored.cookies == session.cookies
        assert restored.user_agent == session.user_agent

    def test_none_returns_none(self):
        assert session_from_db_record(None) is None

    def test_invalid_encrypted_returns_none(self):
        assert session_from_db_record("garbage-data") is None


class TestGetValidSession:
    @pytest.mark.asyncio
    async def test_valid_existing_session(self):
        session = _make_session()
        db_value = session_to_db_value(session)

        scraper = AsyncMock()
        scraper.check_session.return_value = True

        result, was_refreshed = await get_valid_session(scraper, db_value, "user", "pass")
        assert not was_refreshed
        assert result.cookies == session.cookies
        scraper.login.assert_not_called()

    @pytest.mark.asyncio
    async def test_expired_session_triggers_login(self):
        session = _make_session(hours_until_expire=-1)  # already expired
        db_value = session_to_db_value(session)

        new_session = _make_session()
        scraper = AsyncMock()
        scraper.login.return_value = new_session

        result, was_refreshed = await get_valid_session(scraper, db_value, "user", "pass")
        assert was_refreshed
        scraper.login.assert_called_once_with("user", "pass")

    @pytest.mark.asyncio
    async def test_no_existing_session_triggers_login(self):
        new_session = _make_session()
        scraper = AsyncMock()
        scraper.login.return_value = new_session

        result, was_refreshed = await get_valid_session(scraper, None, "user", "pass")
        assert was_refreshed
        scraper.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_session_check_triggers_login(self):
        session = _make_session()
        db_value = session_to_db_value(session)

        new_session = _make_session()
        scraper = AsyncMock()
        scraper.check_session.return_value = False
        scraper.login.return_value = new_session

        result, was_refreshed = await get_valid_session(scraper, db_value, "user", "pass")
        assert was_refreshed
        scraper.login.assert_called_once()
