"""Tests for rate limit middleware."""

import time

import pytest
from pydantic import BaseModel

from mirror_core.middleware import Invocation
from mirror_core.pipeline import Step
from mirror_middleware.ratelimit import RateLimitMiddleware


class RateLimitRequest(BaseModel):
    url: str


@pytest.mark.asyncio
async def test_ratelimit_allows():
    async def mock_next(invocation):
        return "ok"

    middleware = RateLimitMiddleware(rate=10.0, burst=5)
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=RateLimitRequest(url="x"), provider=object())
    start = time.monotonic()
    for _ in range(5):
        result = await middleware(invocation, mock_next)
        assert result == "ok"
    end = time.monotonic()
    assert end - start < 0.1


@pytest.mark.asyncio
async def test_ratelimit_waits():
    async def mock_next(invocation):
        return "ok"

    middleware = RateLimitMiddleware(rate=10.0, burst=2)
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=RateLimitRequest(url="x"), provider=object())
    start = time.monotonic()
    for _ in range(10):
        await middleware(invocation, mock_next)
    end = time.monotonic()
    assert end - start >= 0.3
