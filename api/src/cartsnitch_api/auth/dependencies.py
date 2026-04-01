"""FastAPI dependency injection for authentication.

Validates Better-Auth session tokens from cookies or Bearer header.
Sessions are verified by querying the shared sessions table directly.
"""

from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.config import settings
from cartsnitch_api.database import get_db

# Keep Bearer scheme as optional — Better-Auth primarily uses cookies,
# but we support Bearer tokens for service-to-service or mobile clients.
bearer_scheme = HTTPBearer(auto_error=False)

# Better-Auth session cookie name
SESSION_COOKIE_NAME = "better-auth.session_token"


async def _validate_session_token(token: str, db: AsyncSession) -> UUID:
    """Validate a Better-Auth session token against the sessions table.

    Returns the user_id (as UUID) if the session is valid and not expired.
    Better-Auth v1.5.6+ stores tokens as SHA-256 hashes, so we hash the
    incoming raw token before querying.
    """
    hashed_token = sha256(token.encode("utf-8")).hexdigest()
    result = await db.execute(
        text("SELECT user_id, expires_at FROM sessions WHERE token = :token"),
        {"token": hashed_token},
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )

    user_id, expires_at = row
    if expires_at.tzinfo is None:
        # Treat naive datetimes as UTC
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    return UUID(str(user_id))


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Extract and validate the session token from cookie or Authorization header.

    Checks in order:
    1. Better-Auth session cookie (primary — web clients)
    2. Bearer token in Authorization header (fallback — API clients)
    """
    token: str | None = None

    # 1. Check session cookie
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token:
        token = cookie_token

    # 2. Fall back to Bearer header
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return await _validate_session_token(token, db)


async def verify_service_key(x_service_key: str = Header()) -> None:
    if x_service_key != settings.service_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service key",
        )
