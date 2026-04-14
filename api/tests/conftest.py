"""Shared test fixtures with in-memory SQLite database.

Session-based auth: tests create users and sessions directly in the DB,
matching the Better-Auth session validation flow.
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from cartsnitch_api.config import settings as cartsnitch_settings
from cartsnitch_api.database import get_db
from cartsnitch_api.main import create_app
from cartsnitch_api.models import Base

TEST_JWT_SECRET = secrets.token_urlsafe(32)
TEST_SERVICE_KEY = secrets.token_urlsafe(32)
TEST_FERNET_KEY = "7reF42nmTwbdN21PBoubGp7h_FU8qSimstmlaMLoRK8="


@pytest.fixture(autouse=True)
def setup_test_settings():
    original_jwt = cartsnitch_settings.jwt_secret_key
    original_service = cartsnitch_settings.service_key
    original_fernet = cartsnitch_settings.fernet_key
    cartsnitch_settings.jwt_secret_key = TEST_JWT_SECRET
    cartsnitch_settings.service_key = TEST_SERVICE_KEY
    cartsnitch_settings.fernet_key = TEST_FERNET_KEY
    yield
    cartsnitch_settings.jwt_secret_key = original_jwt
    cartsnitch_settings.service_key = original_service
    cartsnitch_settings.fernet_key = original_fernet


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for all tests to prevent 429 interference."""
    cartsnitch_settings.rate_limit_enabled = False
    yield
    cartsnitch_settings.rate_limit_enabled = True


@pytest.fixture
def engine():
    """Sync in-memory SQLite engine for model unit tests."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    """Sync SQLAlchemy session for model unit tests."""
    factory = sessionmaker(bind=engine)
    with factory() as sess:
        yield sess


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create Better-Auth tables (not managed by SQLAlchemy models)
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                token TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """)
        )
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                access_token_expires_at TIMESTAMP,
                refresh_token_expires_at TIMESTAMP,
                scope TEXT,
                id_token TEXT,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """)
        )
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS verifications (
                id TEXT PRIMARY KEY,
                identifier TEXT NOT NULL,
                value TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """)
        )

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _create_test_user_and_session(
    client: AsyncClient, db_engine, **user_overrides
) -> tuple[dict, str]:
    """Create a test user and a valid session directly in the DB.

    Returns (user_dict, session_token).  Better-Auth stores the raw token
    in the DB, so we insert it as-is.
    """
    user_id = str(uuid.uuid4())
    email = user_overrides.get("email", "test@example.com")
    display_name = user_overrides.get("display_name", "Test User")
    session_token = secrets.token_urlsafe(32)
    session_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    expires = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, display_name, email_verified, created_at, updated_at) "
                "VALUES (:id, :email, :hashed_password, :display_name, :email_verified, :created_at, :updated_at)"
            ),
            {
                "id": user_id,
                "email": email,
                "hashed_password": "not-used-with-better-auth",
                "display_name": display_name,
                "email_verified": False,
                "created_at": now,
                "updated_at": now,
            },
        )
        await conn.execute(
            text(
                "INSERT INTO sessions (id, token, user_id, expires_at, created_at, updated_at) "
                "VALUES (:id, :token, :user_id, :expires_at, :created_at, :updated_at)"
            ),
            {
                "id": session_id,
                "token": session_token,
                "user_id": user_id,
                "expires_at": expires,
                "created_at": now,
                "updated_at": now,
            },
        )

    return {"id": user_id, "email": email, "display_name": display_name}, session_token


@pytest.fixture
async def auth_headers(client, db_engine):
    """Create a test user with a valid session and return auth headers."""
    _, session_token = await _create_test_user_and_session(client, db_engine)
    return {"Cookie": f"better-auth.session_token={session_token}"}
