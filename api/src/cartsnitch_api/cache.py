"""Redis/DragonflyDB caching helpers."""

from cartsnitch_api.config import settings


class CacheClient:
    """Stub for Redis/DragonflyDB caching.

    Will be used for expensive queries: price trends, product comparisons.
    Cache invalidation via Redis pub/sub events from other services.
    """

    def __init__(self) -> None:
        self.url = settings.redis_url

    async def get(self, key: str) -> str | None:
        # TODO: implement with redis-py async
        return None

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        # TODO: implement with redis-py async
        pass

    async def delete(self, key: str) -> None:
        # TODO: implement with redis-py async
        pass
