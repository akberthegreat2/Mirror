"""Tests for retry middleware."""

import asyncio

import pytest
from mirror_middleware.retry import RetryMiddleware


@pytest.mark.asyncio
async def test_retry_success():
    attempts = 0

    async def mock_next(invocation):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("temporary error")
        return "success"

    middleware = RetryMiddleware(max_attempts=5, base_delay=0.01)
    result = await middleware({}, mock_next)
    assert result == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    attempts = 0

    async def mock_next(invocation):
        nonlocal attempts
        attempts += 1
        raise ValueError("always fails")

    middleware = RetryMiddleware(max_attempts=3, base_delay=0.01)
    with pytest.raises(ValueError, match="always fails"):
        await middleware({}, mock_next)
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_cancellation():
    async def mock_next(invocation):
        raise asyncio.CancelledError()

    middleware = RetryMiddleware(max_attempts=3)
    with pytest.raises(asyncio.CancelledError):
        await middleware({}, mock_next)
