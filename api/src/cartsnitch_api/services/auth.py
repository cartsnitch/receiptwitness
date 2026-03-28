"""Auth service — user registration, login, token management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.jwt import create_access_token, create_refresh_token, decode_token
from cartsnitch_api.auth.passwords import hash_password, verify_password
from cartsnitch_api.config import settings


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, email: str, password: str, display_name: str) -> dict:
        from cartsnitch_api.models import User

        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            display_name=display_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return self._make_token_response(user.id)

    async def login(self, email: str, password: str) -> dict:
        from cartsnitch_api.models import User

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        return self._make_token_response(user.id)

    async def refresh(self, refresh_token: str) -> dict:
        from cartsnitch_api.models import User

        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise ValueError("Invalid refresh token") from None

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type") from None

        user_id = UUID(payload["sub"])

        # Verify the user still exists before issuing new tokens
        result = await self.db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            raise ValueError("User no longer exists")

        return self._make_token_response(user_id)

    async def get_user(self, user_id: UUID) -> dict:
        from cartsnitch_api.models import User

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise LookupError("User not found")

        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "created_at": user.created_at,
        }

    async def update_user(self, user_id: UUID, **fields) -> dict:
        from cartsnitch_api.models import User

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise LookupError("User not found")

        if "display_name" in fields and fields["display_name"] is not None:
            user.display_name = fields["display_name"]
        if "email" in fields and fields["email"] is not None:
            existing = await self.db.execute(
                select(User).where(User.email == fields["email"], User.id != user_id)
            )
            if existing.scalar_one_or_none():
                raise ValueError("Email already in use")
            user.email = fields["email"]

        await self.db.commit()
        await self.db.refresh(user)

        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "created_at": user.created_at,
        }

    async def delete_user(self, user_id: UUID) -> None:
        from cartsnitch_api.models import User

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise LookupError("User not found")

        await self.db.delete(user)
        await self.db.commit()

    def _make_token_response(self, user_id: UUID) -> dict:
        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id),
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }
