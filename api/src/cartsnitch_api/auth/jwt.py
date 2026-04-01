"""JWT token creation and validation."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt

from cartsnitch_api.config import settings


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return cast(str, jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return cast(str, jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def decode_token(token: str) -> dict:
    try:
        return cast(
            dict[str, Any],
            jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]),
        )
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
