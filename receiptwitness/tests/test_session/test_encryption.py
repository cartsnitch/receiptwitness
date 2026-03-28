"""Tests for session encryption/decryption."""

from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken

from receiptwitness.session.encryption import decrypt_session_data, encrypt_session_data

TEST_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _mock_encryption_key():
    with patch("receiptwitness.session.encryption.settings") as mock_settings:
        mock_settings.session_encryption_key = TEST_KEY
        yield


class TestEncryptDecrypt:
    def test_roundtrip(self):
        data = {
            "cookies": [{"name": "session", "value": "abc123", "domain": ".meijer.com"}],
            "user_agent": "Mozilla/5.0",
        }
        encrypted = encrypt_session_data(data)
        assert isinstance(encrypted, str)
        assert encrypted != str(data)

        decrypted = decrypt_session_data(encrypted)
        assert decrypted == data

    def test_different_data_different_ciphertext(self):
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        enc1 = encrypt_session_data(data1)
        enc2 = encrypt_session_data(data2)
        assert enc1 != enc2

    def test_decrypt_with_wrong_key_fails(self):
        data = {"cookies": []}
        encrypted = encrypt_session_data(data)

        wrong_key = Fernet.generate_key().decode()
        with patch("receiptwitness.session.encryption.settings") as mock_settings:
            mock_settings.session_encryption_key = wrong_key
            with pytest.raises(InvalidToken):
                decrypt_session_data(encrypted)

    def test_decrypt_tampered_data_fails(self):
        data = {"cookies": []}
        encrypted = encrypt_session_data(data)
        tampered = encrypted[:-5] + "XXXXX"
        with pytest.raises(Exception):
            decrypt_session_data(tampered)

    def test_no_key_raises_error(self):
        with patch("receiptwitness.session.encryption.settings") as mock_settings:
            mock_settings.session_encryption_key = ""
            with pytest.raises(ValueError, match="RW_SESSION_ENCRYPTION_KEY"):
                encrypt_session_data({"test": True})
