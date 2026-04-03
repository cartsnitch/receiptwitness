"""Auth service — user profile management.

Registration, login, token management, and session handling are now
handled by the Better-Auth service (auth/). This service provides
user lookup and profile update operations for the API gateway.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user(self, user_id: str) -> dict:
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

    async def update_user(self, user_id: str, **fields) -> dict:
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

    async def delete_user(self, user_id: str) -> None:
        from cartsnitch_api.models import User

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise LookupError("User not found")

        await self.db.delete(user)
        await self.db.commit()

    async def get_email_in_address(self, user_id: str) -> str:
        """Return the per-user email-in address for receipt forwarding."""
        from cartsnitch_api.models import User

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise LookupError("User not found")

        return f"{user.email_inbound_token}@email.cartsnitch.com"
