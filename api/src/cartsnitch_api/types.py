"""Custom SQLAlchemy column types."""

import json

from cryptography.fernet import Fernet
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from cartsnitch_api.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.fernet_key.encode())


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts JSON using Fernet.

    Stores data as a Fernet-encrypted text blob in the database.
    On read, decrypts and deserialises back to a Python dict/list.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        plaintext = json.dumps(value).encode()
        return _get_fernet().encrypt(plaintext).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        decrypted = _get_fernet().decrypt(value.encode())
        return json.loads(decrypted)
