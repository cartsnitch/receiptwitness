"""Tests for EncryptedJSON TypeDecorator and session_data encryption."""

import json

import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError
from sqlalchemy import column, create_engine, table, text
from sqlalchemy.orm import sessionmaker

from cartsnitch_api.config import settings
from cartsnitch_api.models import Base
from cartsnitch_api.models.store import Store
from cartsnitch_api.models.user import User, UserStoreAccount


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    factory = sessionmaker(bind=engine)
    with factory() as sess:
        yield sess


@pytest.fixture
def store(session):
    s = Store(name="Test Store", slug="test-store")
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


@pytest.fixture
def user(session):
    u = User(email="alice@example.com", hashed_password="fakehash")
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


class TestEncryptedJSONType:
    """Unit tests for the EncryptedJSON TypeDecorator."""

    def test_round_trip(self, session, user, store):
        """Data written via the ORM comes back as the original dict."""
        original = {"token": "abc123", "cookies": {"session_id": "xyz"}}
        account = UserStoreAccount(user_id=user.id, store_id=store.id, session_data=original)
        session.add(account)
        session.commit()

        loaded = session.get(UserStoreAccount, account.id)
        assert loaded.session_data == original

    def test_stored_value_is_encrypted(self, session, user, store):
        """The raw value in the DB should be a Fernet token, not plaintext JSON."""
        original = {"secret": "do-not-leak"}
        account = UserStoreAccount(user_id=user.id, store_id=store.id, session_data=original)
        session.add(account)
        session.commit()

        # Use a raw table construct to bypass TypeDecorator on read
        raw_table = table("user_store_accounts", column("id"), column("session_data"))
        raw = session.execute(raw_table.select().where(raw_table.c.id == str(account.id))).first()
        # If UUID matching fails with str, try bytes format
        if raw is None:
            raw = session.execute(
                text("SELECT session_data FROM user_store_accounts LIMIT 1")
            ).scalar_one()
        else:
            raw = raw[1]

        assert raw != json.dumps(original)
        assert raw.startswith("gAAAAA")

        # Verify we can decrypt the raw value manually
        f = Fernet(settings.fernet_key.encode())
        decrypted = json.loads(f.decrypt(raw.encode()))
        assert decrypted == original

    def test_null_round_trip(self, session, user, store):
        """NULL session_data stays NULL."""
        account = UserStoreAccount(user_id=user.id, store_id=store.id, session_data=None)
        session.add(account)
        session.commit()

        loaded = session.get(UserStoreAccount, account.id)
        assert loaded.session_data is None

    def test_empty_dict_round_trip(self, session, user, store):
        """Empty dict round-trips correctly."""
        account = UserStoreAccount(user_id=user.id, store_id=store.id, session_data={})
        session.add(account)
        session.commit()

        loaded = session.get(UserStoreAccount, account.id)
        assert loaded.session_data == {}

    def test_update_session_data(self, session, user, store):
        """Updating session_data re-encrypts the new value."""
        account = UserStoreAccount(user_id=user.id, store_id=store.id, session_data={"v": 1})
        session.add(account)
        session.commit()

        account.session_data = {"v": 2, "new_field": True}
        session.commit()

        loaded = session.get(UserStoreAccount, account.id)
        assert loaded.session_data == {"v": 2, "new_field": True}


class TestEncryptionKeyValidation:
    """Test that invalid/missing keys are caught at startup."""

    def test_invalid_fernet_key_rejected(self, monkeypatch):
        """Settings validation rejects a bad key."""
        monkeypatch.setenv("CARTSNITCH_FERNET_KEY", "not-a-valid-key")

        with pytest.raises(ValidationError):
            from cartsnitch_api.config import Settings

            Settings()
