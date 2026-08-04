"""Tests for retry middleware."""

import asyncio

import pytest
from pydantic import BaseModel

from mirror_core.middleware import Invocation
from mirror_core.pipeline import Step
from mirror_middleware.retry import RetryMiddleware


class RetryRequest(BaseModel):
    url: str


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
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=RetryRequest(url="x"), provider=object())
    result = await middleware(invocation, mock_next)
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
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=RetryRequest(url="x"), provider=object())
    with pytest.raises(ValueError, match="always fails"):
        await middleware(invocation, mock_next)
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_cancellation():
    async def mock_next(invocation):
        raise asyncio.CancelledError()

    middleware = RetryMiddleware(max_attempts=3)
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=RetryRequest(url="x"), provider=object())
    with pytest.raises(asyncio.CancelledError):
        await middleware(invocation, mock_next)
