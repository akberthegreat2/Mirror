"""Tests for logging middleware."""

import logging

import pytest
from mirror_middleware.logging import LoggingMiddleware


@pytest.mark.asyncio
async def test_logging_success(caplog):
    caplog.set_level(logging.DEBUG)

    async def mock_next(invocation):
        return "ok"

    middleware = LoggingMiddleware(level="debug")
    result = await middleware({"step": {"id": "test", "capability": "fetch"}}, mock_next)
    assert result == "ok"
    assert "Invoking capability 'fetch'" in caplog.text
    assert "succeeded" in caplog.text


@pytest.mark.asyncio
async def test_logging_error(caplog):
    caplog.set_level(logging.DEBUG)

    async def mock_next(invocation):
        raise ValueError("oops")

    middleware = LoggingMiddleware(level="debug")
    with pytest.raises(ValueError):
        await middleware({"step": {"id": "test", "capability": "fetch"}}, mock_next)
    assert "failed" in caplog.text
    assert "oops" in caplog.text
