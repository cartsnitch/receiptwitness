"""Store service — list stores, manage user store account connections."""

import json
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cartsnitch_api.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.fernet_key.encode())


class StoreService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_stores(self) -> list[dict]:
        from cartsnitch_api.models import Store

        result = await self.db.execute(select(Store).order_by(Store.name))
        stores = result.scalars().all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "logo_url": s.logo_url,
                "supported": True,
            }
            for s in stores
        ]

    async def list_user_stores(self, user_id: UUID) -> list[dict]:
        from cartsnitch_api.models import UserStoreAccount

        result = await self.db.execute(
            select(UserStoreAccount)
            .where(UserStoreAccount.user_id == user_id)
            .options(selectinload(UserStoreAccount.store))
        )
        accounts = result.scalars().all()
        return [
            {
                "store": {
                    "id": a.store.id,
                    "name": a.store.name,
                    "slug": a.store.slug,
                    "logo_url": a.store.logo_url,
                    "supported": True,
                },
                "connected": a.status == "active",
                "last_sync_at": a.last_sync_at,
                "sync_status": a.status,
            }
            for a in accounts
        ]

    async def connect_store(self, user_id: UUID, store_slug: str, credentials: dict | None) -> dict:
        from cartsnitch_api.models import Store, UserStoreAccount

        result = await self.db.execute(select(Store).where(Store.slug == store_slug))
        store = result.scalar_one_or_none()
        if not store:
            raise LookupError(f"Store '{store_slug}' not found")

        existing = await self.db.execute(
            select(UserStoreAccount).where(
                UserStoreAccount.user_id == user_id,
                UserStoreAccount.store_id == store.id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Store account already connected")

        encrypted_data = None
        if credentials:
            fernet = _get_fernet()
            encrypted_data = {
                "encrypted": fernet.encrypt(json.dumps(credentials).encode()).decode()
            }

        account = UserStoreAccount(
            user_id=user_id,
            store_id=store.id,
            session_data=encrypted_data,
            status="active",
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        return {
            "store": {
                "id": store.id,
                "name": store.name,
                "slug": store.slug,
                "logo_url": store.logo_url,
                "supported": True,
            },
            "connected": True,
            "last_sync_at": None,
            "sync_status": "active",
        }

    async def disconnect_store(self, user_id: UUID, store_slug: str) -> None:
        from cartsnitch_api.models import Store, UserStoreAccount

        result = await self.db.execute(select(Store).where(Store.slug == store_slug))
        store = result.scalar_one_or_none()
        if not store:
            raise LookupError(f"Store '{store_slug}' not found")

        result = await self.db.execute(
            select(UserStoreAccount).where(
                UserStoreAccount.user_id == user_id,
                UserStoreAccount.store_id == store.id,
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise LookupError("Store account not connected")

        await self.db.delete(account)
        await self.db.commit()
