"""Tests for timeout middleware."""

import asyncio

import pytest
from pydantic import BaseModel

from mirror_core.middleware import Invocation
from mirror_core.pipeline import Step
from mirror_middleware.timeout import TimeoutMiddleware


class TimeoutRequest(BaseModel):
    url: str


@pytest.mark.asyncio
async def test_timeout_success():
    async def mock_next(invocation):
        await asyncio.sleep(0.01)
        return "done"

    middleware = TimeoutMiddleware(timeout=1.0)
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=TimeoutRequest(url="x"), provider=object())
    result = await middleware(invocation, mock_next)
    assert result == "done"


@pytest.mark.asyncio
async def test_timeout_exceeded():
    async def mock_next(invocation):
        await asyncio.sleep(0.1)
        return "done"

    middleware = TimeoutMiddleware(timeout=0.01)
    invocation = Invocation(step=Step(id="test", capability="fetch"), request=TimeoutRequest(url="x"), provider=object())
    with pytest.raises(TimeoutError):
        await middleware(invocation, mock_next)
