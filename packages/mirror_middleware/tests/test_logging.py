"""Tests for logging middleware."""

import logging

import pytest
from pydantic import BaseModel

from mirror_core.middleware import Invocation
from mirror_core.pipeline import Step
from mirror_middleware.logging import LoggingMiddleware


class LoggingRequest(BaseModel):
    url: str


@pytest.mark.asyncio
async def test_logging_success(caplog):
    caplog.set_level(logging.DEBUG)

    async def mock_next(invocation):
        return "ok"

    middleware = LoggingMiddleware(level="debug")
    invocation = Invocation(
        step=Step(id="test", capability="fetch"),
        request=LoggingRequest(url="https://example.com"),
        provider=object(),
    )
    result = await middleware(invocation, mock_next)
    assert result == "ok"
    assert "Invoking capability 'fetch'" in caplog.text
    assert "succeeded" in caplog.text


@pytest.mark.asyncio
async def test_logging_error(caplog):
    caplog.set_level(logging.DEBUG)

    async def mock_next(invocation):
        raise ValueError("oops")

    middleware = LoggingMiddleware(level="debug")
    invocation = Invocation(
        step=Step(id="test", capability="fetch"),
        request=LoggingRequest(url="https://example.com"),
        provider=object(),
    )
    with pytest.raises(ValueError):
        await middleware(invocation, mock_next)
    assert "failed" in caplog.text
    assert "oops" in caplog.text
