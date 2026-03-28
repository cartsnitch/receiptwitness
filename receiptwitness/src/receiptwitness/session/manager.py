"""Session storage, retrieval, and refresh logic.

Manages the lifecycle of retailer session data:
- Load encrypted session from DB
- Check validity via scraper
- Re-authenticate if expired
- Save new session back (encrypted)
"""

import logging
from dataclasses import asdict
from datetime import UTC, datetime

from receiptwitness.scrapers.base import BaseScraper, SessionData
from receiptwitness.session.encryption import decrypt_session_data, encrypt_session_data

logger = logging.getLogger(__name__)


def session_from_db_record(session_data_encrypted: str | None) -> SessionData | None:
    """Deserialize and decrypt a session from the database.

    The session_data column in user_store_accounts stores the Fernet-encrypted
    JSON of the SessionData fields.
    """
    if not session_data_encrypted:
        return None

    try:
        data = decrypt_session_data(session_data_encrypted)
        return SessionData(
            cookies=data["cookies"],
            user_agent=data["user_agent"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            extra=data.get("extra", {}),
        )
    except Exception:
        logger.exception("Failed to load session from DB record")
        return None


def session_to_db_value(session: SessionData) -> str:
    """Serialize and encrypt a session for database storage."""
    data = asdict(session)
    # Convert datetime objects to ISO strings for JSON serialization
    data["created_at"] = session.created_at.isoformat()
    if session.expires_at:
        data["expires_at"] = session.expires_at.isoformat()
    return encrypt_session_data(data)


async def get_valid_session(
    scraper: BaseScraper,
    session_data_encrypted: str | None,
    username: str,
    password: str,
) -> tuple[SessionData, bool]:
    """Get a valid session, re-authenticating if needed.

    Returns:
        A tuple of (session, was_refreshed). If was_refreshed is True,
        the caller should persist the new session to the database.
    """
    # Try existing session first
    existing = session_from_db_record(session_data_encrypted)
    if existing:
        if existing.expires_at and datetime.now(UTC) > existing.expires_at:
            logger.info("Session expired by timestamp, re-authenticating")
        elif await scraper.check_session(existing):
            logger.info("Existing session is valid")
            return existing, False
        else:
            logger.info("Session check failed, re-authenticating")

    # Need to re-authenticate
    logger.info("Performing fresh login")
    new_session = await scraper.login(username, password)
    return new_session, True
