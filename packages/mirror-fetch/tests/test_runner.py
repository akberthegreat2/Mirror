"""Tests for fetch runner."""

from unittest.mock import AsyncMock

import pytest
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.runner import fetch_step


@pytest.mark.asyncio
async def test_fetch_step_success():
    mock_provider = AsyncMock()
    request = FetchRequest(url="https://example.com")
    expected = FetchResult(
        url="https://example.com",
        status_code=200,
        content=b"ok",
        fetch_duration=0.1,
        timestamp="2026-08-03T12:00:00Z",
    )
    mock_provider.fetch.return_value = expected

    result = await fetch_step(mock_provider, request)
    mock_provider.fetch.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_fetch_step_raises_fetch_error():
    mock_provider = AsyncMock()
    mock_provider.fetch.side_effect = FetchError("provider error")
    request = FetchRequest(url="https://example.com")

    with pytest.raises(FetchError, match="provider error"):
        await fetch_step(mock_provider, request)


@pytest.mark.asyncio
async def test_fetch_step_wraps_unknown_error():
    mock_provider = AsyncMock()
    mock_provider.fetch.side_effect = ValueError("unexpected")
    request = FetchRequest(url="https://example.com")

    with pytest.raises(FetchError) as exc:
        await fetch_step(mock_provider, request)
    assert "unexpected" in str(exc.value)
    assert exc.value.cause is not None
