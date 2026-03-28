"""HTTP client for ShrinkRay internal API."""

from typing import Any, cast

import httpx

from cartsnitch_api.config import settings


class ShrinkRayClient:
    def __init__(self) -> None:
        self.base_url = settings.shrinkray_url
        self.headers = {"X-Service-Key": settings.service_key}

    async def get_shrinkflation_alerts(self, user_id: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/alerts",
                headers=self.headers,
                params={"user_id": user_id},
            )
            resp.raise_for_status()
            return cast(list[dict[str, Any]], resp.json())
