"""Tests for rate limit middleware."""

import time

import pytest
from mirror_middleware.ratelimit import RateLimitMiddleware


@pytest.mark.asyncio
async def test_ratelimit_allows():
    async def mock_next(invocation):
        return "ok"

    middleware = RateLimitMiddleware(rate=10.0, burst=5)
    start = time.monotonic()
    for _ in range(5):
        result = await middleware({}, mock_next)
        assert result == "ok"
    end = time.monotonic()
    assert end - start < 0.1  # Should be fast within burst


@pytest.mark.asyncio
async def test_ratelimit_waits():
    async def mock_next(invocation):
        return "ok"

    middleware = RateLimitMiddleware(rate=10.0, burst=2)
    start = time.monotonic()
    for _ in range(10):
        await middleware({}, mock_next)
    end = time.monotonic()
    # Should take roughly (10-2)/10 = 0.8 seconds
    assert end - start >= 0.3
