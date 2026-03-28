"""HTTP client for StickerShock internal API."""

from typing import Any, cast

import httpx

from cartsnitch_api.config import settings


class StickerShockClient:
    def __init__(self) -> None:
        self.base_url = settings.stickershock_url
        self.headers = {"X-Service-Key": settings.service_key}

    async def get_price_increases(self, params: dict | None = None) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/increases",
                headers=self.headers,
                params=params,
            )
            resp.raise_for_status()
            return cast(list[dict[str, Any]], resp.json())

    async def get_inflation_data(self) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/inflation",
                headers=self.headers,
            )
            resp.raise_for_status()
            return cast(dict[str, Any], resp.json())
