"""Tests for timeout middleware."""

import asyncio

import pytest
from mirror_middleware.timeout import TimeoutMiddleware


@pytest.mark.asyncio
async def test_timeout_success():
    async def mock_next(invocation):
        await asyncio.sleep(0.01)
        return "done"

    middleware = TimeoutMiddleware(timeout=1.0)
    result = await middleware({}, mock_next)
    assert result == "done"


@pytest.mark.asyncio
async def test_timeout_exceeded():
    async def mock_next(invocation):
        await asyncio.sleep(0.1)
        return "done"

    middleware = TimeoutMiddleware(timeout=0.01)
    with pytest.raises(TimeoutError):
        await middleware({}, mock_next)
