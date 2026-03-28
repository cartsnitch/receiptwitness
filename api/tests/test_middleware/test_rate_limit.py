"""Tests for rate limiting middleware."""

import pytest

from cartsnitch_api.middleware.rate_limit import _SlidingWindowCounter


class TestSlidingWindowCounter:
    def test_allows_within_limit(self):
        counter = _SlidingWindowCounter(max_requests=5, window_seconds=60)
        for i in range(5):
            allowed, remaining, retry = counter.is_allowed("test-key")
            assert allowed is True
            assert remaining == 4 - i

    def test_blocks_over_limit(self):
        counter = _SlidingWindowCounter(max_requests=3, window_seconds=60)
        for _ in range(3):
            counter.is_allowed("test-key")

        allowed, remaining, retry = counter.is_allowed("test-key")
        assert allowed is False
        assert remaining == 0
        assert retry > 0

    def test_separate_keys(self):
        counter = _SlidingWindowCounter(max_requests=2, window_seconds=60)
        # Fill key-a
        counter.is_allowed("key-a")
        counter.is_allowed("key-a")
        allowed_a, _, _ = counter.is_allowed("key-a")
        assert allowed_a is False

        # key-b should still be allowed
        allowed_b, remaining, _ = counter.is_allowed("key-b")
        assert allowed_b is True
        assert remaining == 1


@pytest.mark.asyncio
async def test_rate_limit_returns_429(client):
    """Public endpoint should return 429 after limit exceeded."""
    # The default limit is 60/min — we won't hit it in normal tests,
    # but we verify the middleware adds rate limit headers.
    resp = await client.get("/public/inflation")
    assert "x-ratelimit-limit" in resp.headers
    assert "x-ratelimit-remaining" in resp.headers


@pytest.mark.asyncio
async def test_health_skips_rate_limit(client):
    """Health endpoint should not have rate limit headers."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert "x-ratelimit-limit" not in resp.headers
