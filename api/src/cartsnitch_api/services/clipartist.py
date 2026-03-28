"""HTTP client for ClipArtist internal API."""

from typing import Any, cast

import httpx

from cartsnitch_api.config import settings


class ClipArtistClient:
    def __init__(self) -> None:
        self.base_url = settings.clipartist_url
        self.headers = {"X-Service-Key": settings.service_key}

    async def optimize(
        self,
        user_id: str,
        items: list[dict],
        preferred_stores: list[str] | None = None,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/optimize",
                headers=self.headers,
                json={
                    "user_id": user_id,
                    "items": items,
                    "preferred_stores": preferred_stores,
                },
            )
            resp.raise_for_status()
            return cast(dict[str, Any], resp.json())

    async def get_shopping_lists(self, user_id: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/shopping-lists",
                headers=self.headers,
                params={"user_id": user_id},
            )
            resp.raise_for_status()
            return cast(list[dict[str, Any]], resp.json())

    async def get_relevant_coupons(self, user_id: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/coupons/relevant",
                headers=self.headers,
                params={"user_id": user_id},
            )
            resp.raise_for_status()
            return cast(list[dict[str, Any]], resp.json())
