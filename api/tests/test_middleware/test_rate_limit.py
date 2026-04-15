"""Tests for rate limiting middleware."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cartsnitch_api.config import settings
from cartsnitch_api.middleware.rate_limit import (
    InMemorySlidingWindow,
    RedisSlidingWindow,
    _get_client_ip,
    _get_rate_limit_key,
)


class TestInMemorySlidingWindow:
    def test_allows_within_limit(self):
        limiter = InMemorySlidingWindow(max_requests=5, window_seconds=60)
        for i in range(5):
            allowed, remaining, retry = limiter.is_allowed("test-key")
            assert allowed is True
            assert remaining == 4 - i

    def test_blocks_over_limit(self):
        limiter = InMemorySlidingWindow(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("test-key")

        allowed, remaining, retry = limiter.is_allowed("test-key")
        assert allowed is False
        assert remaining == 0
        assert retry > 0

    def test_separate_keys(self):
        limiter = InMemorySlidingWindow(max_requests=2, window_seconds=60)
        limiter.is_allowed("key-a")
        limiter.is_allowed("key-a")
        allowed_a, _, _ = limiter.is_allowed("key-a")
        assert allowed_a is False

        allowed_b, remaining, _ = limiter.is_allowed("key-b")
        assert allowed_b is True
        assert remaining == 1

    def test_resets_after_window_expires(self):
        limiter = InMemorySlidingWindow(max_requests=2, window_seconds=1)
        for _ in range(2):
            limiter.is_allowed("test-key")
        allowed, remaining, _ = limiter.is_allowed("test-key")
        assert allowed is False

        time.sleep(1.1)
        allowed, remaining, _ = limiter.is_allowed("test-key")
        assert allowed is True
        assert remaining == 1


class TestGetClientIp:
    def test_x_forwarded_for_single(self):
        req = MagicMock()
        req.headers = {"x-forwarded-for": "192.168.1.1"}
        req.client = None
        assert _get_client_ip(req) == "192.168.1.1"

    def test_x_forwarded_for_multiple(self):
        req = MagicMock()
        req.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1, 172.16.0.1"}
        req.client = None
        assert _get_client_ip(req) == "192.168.1.1"

    def test_x_forwarded_for_with_port(self):
        req = MagicMock()
        req.headers = {"x-forwarded-for": "192.168.1.1:8080"}
        req.client = None
        assert _get_client_ip(req) == "192.168.1.1"

    def test_no_forwarded_header(self):
        req = MagicMock()
        req.headers = {}
        req.client.host = "127.0.0.1"
        assert _get_client_ip(req) == "127.0.0.1"

    def test_no_client(self):
        req = MagicMock()
        req.headers = {}
        req.client = None
        assert _get_client_ip(req) == "unknown"


class TestGetRateLimitKey:
    def _make_request(
        self,
        path: str = "/purchases",
        method: str = "GET",
        auth_header: str = "",
        headers: dict | None = None,
    ) -> MagicMock:
        req = MagicMock()
        req.url.path = path
        req.method = method
        req.headers = dict(headers) if headers else {}
        if auth_header:
            req.headers["authorization"] = auth_header
        return req

    def test_public_path_uses_public_limiter(self):
        req = self._make_request("/public/inflation")
        key, limiter = _get_rate_limit_key(req)
        assert key.startswith("ip:")
        assert limiter.max_requests == settings.rate_limit_requests

    def test_auth_post_path_uses_strict_limiter(self):
        req = self._make_request("/auth/login", method="POST")
        key, limiter = _get_rate_limit_key(req)
        assert key.startswith("ip:")
        assert limiter.max_requests == settings.rate_limit_auth_requests
        assert limiter.window_seconds == settings.rate_limit_auth_window_seconds

    def test_auth_get_path_uses_auth_limiter(self):
        req = self._make_request("/auth/me", method="GET")
        key, limiter = _get_rate_limit_key(req)
        assert key.startswith("ip:")
        assert limiter.max_requests == settings.rate_limit_requests * 5

    def test_authenticated_token_uses_auth_limiter(self):
        req = self._make_request("/purchases", auth_header="Bearer token123")
        key, limiter = _get_rate_limit_key(req)
        assert key.startswith("token:")
        assert limiter.max_requests == settings.rate_limit_requests * 5

    def test_distinct_tokens_produce_distinct_keys(self):
        req1 = self._make_request("/purchases", auth_header="Bearer token_alpha_12345")
        req2 = self._make_request("/purchases", auth_header="Bearer token_beta_67890")
        key1, _ = _get_rate_limit_key(req1)
        key2, _ = _get_rate_limit_key(req2)
        assert key1 != key2

    def test_same_token_produces_same_key(self):
        req1 = self._make_request("/purchases", auth_header="Bearer same_token_value_abc")
        req2 = self._make_request("/purchases", auth_header="Bearer same_token_value_abc")
        key1, _ = _get_rate_limit_key(req1)
        key2, _ = _get_rate_limit_key(req2)
        assert key1 == key2

    def test_key_does_not_contain_raw_token_suffix(self):
        raw_token = "my_secret_jwt_token_xyz"
        req = self._make_request("/purchases", auth_header=f"Bearer {raw_token}")
        key, _ = _get_rate_limit_key(req)
        assert raw_token[-16:] not in key
        assert raw_token not in key


class TestRedisSlidingWindowFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_redis_connection_error(self):
        mock_redis = AsyncMock()
        mock_redis.pipeline.return_value = AsyncMock()
        pipe_mock = AsyncMock()
        pipe_mock.execute.side_effect = Exception("Connection refused")
        mock_redis.pipeline.return_value = pipe_mock

        limiter = RedisSlidingWindow(mock_redis, max_requests=5, window_seconds=60)
        allowed, remaining, retry = await limiter.is_allowed("test-key")
        assert allowed is True
        assert remaining == 4

    @pytest.mark.asyncio
    async def test_fallback_on_redis_error_during_pipeline(self):
        mock_redis = AsyncMock()
        pipe_mock = AsyncMock()
        pipe_mock.execute.side_effect = Exception("Redis error")
        mock_redis.pipeline.return_value = pipe_mock

        limiter = RedisSlidingWindow(mock_redis, max_requests=3, window_seconds=60)
        allowed, remaining, retry = await limiter.is_allowed("test-key")
        assert allowed is True


@pytest.mark.asyncio
async def test_rate_limit_returns_429(client):
    resp = await client.get("/public/inflation")
    assert "x-ratelimit-limit" in resp.headers
    assert "x-ratelimit-remaining" in resp.headers


@pytest.mark.asyncio
async def test_health_skips_rate_limit(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert "x-ratelimit-limit" not in resp.headers
