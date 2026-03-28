"""Fernet-based encryption for session cookies at rest.

Session data (cookies, tokens) is encrypted before writing to the database
and decrypted only when needed for a scrape. The encryption key is provided
via the RW_SESSION_ENCRYPTION_KEY environment variable — it is never stored
in the database or logged.
"""

import json
import logging

from cryptography.fernet import Fernet, InvalidToken

from receiptwitness.config import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Get a Fernet instance using the configured encryption key."""
    key = settings.session_encryption_key
    if not key:
        raise ValueError(
            "RW_SESSION_ENCRYPTION_KEY is not set. "
            "Generate one with: "
            "python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_session_data(data: dict) -> str:
    """Encrypt session data dict to a Fernet token string.

    The data is JSON-serialized, then encrypted. The result is a
    URL-safe base64-encoded string suitable for storing in JSONB.
    """
    f = _get_fernet()
    plaintext = json.dumps(data, default=str).encode("utf-8")
    return f.encrypt(plaintext).decode("utf-8")


def decrypt_session_data(encrypted: str) -> dict:
    """Decrypt a Fernet token string back to a session data dict."""
    f = _get_fernet()
    try:
        plaintext = f.decrypt(encrypted.encode("utf-8"))
        result: dict = json.loads(plaintext)
        return result
    except InvalidToken:
        logger.error("Failed to decrypt session data — invalid token or wrong key")
        raise
