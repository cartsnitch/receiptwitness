"""Tests for Settings config, specifically the database_url env var fallback."""

import os

from cartsnitch_api.config import Settings


def test_database_url_prefers_cartsnitch_prefix():
    """CARTSNITCH_DATABASE_URL takes precedence over DATABASE_URL."""
    env = {
        "CARTSNITCH_DATABASE_URL": "postgresql+asyncpg://user1:pass1@host1:5432/db1",
        "DATABASE_URL": "postgresql://user2:pass2@host2:5432/db2",
    }
    settings = Settings(**env)
    assert settings.database_url == "postgresql+asyncpg://user1:pass1@host1:5432/db1"


def test_database_url_falls_back_to_database_url():
    """When CARTSNITCH_DATABASE_URL is absent, DATABASE_URL is accepted."""
    env = {
        "DATABASE_URL": "postgresql://user:pass@dbhost:5432/mydb",
    }
    settings = Settings(**env)
    assert settings.database_url == "postgresql+asyncpg://user:pass@dbhost:5432/mydb"


def test_database_url_normalizes_plain_postgresql_prefix():
    """DATABASE_URL with plain postgresql:// is normalized to postgresql+asyncpg://."""
    env = {
        "DATABASE_URL": "postgresql://cartsnitch:cartsnitch@localhost:5432/cartsnitch",
    }
    settings = Settings(**env)
    assert settings.database_url == "postgresql+asyncpg://cartsnitch:cartsnitch@localhost:5432/cartsnitch"


def test_database_url_preserves_asyncpg_prefix():
    """CARTSNITCH_DATABASE_URL with postgresql+asyncpg:// is left unchanged."""
    env = {
        "CARTSNITCH_DATABASE_URL": "postgresql+asyncpg://cartsnitch:cartsnitch@localhost:5432/cartsnitch",
    }
    settings = Settings(**env)
    assert settings.database_url == "postgresql+asyncpg://cartsnitch:cartsnitch@localhost:5432/cartsnitch"


def test_database_url_default():
    """When neither env var is set, the hardcoded default is used."""
    settings = Settings()
    assert settings.database_url == "postgresql+asyncpg://cartsnitch:cartsnitch@localhost:5432/cartsnitch"
