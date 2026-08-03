"""Tests for HTTPX provider."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest
from mirror_fetch_httpx.provider import HTTPXProvider


@pytest.mark.asyncio
async def test_fetch_success():
    provider = HTTPXProvider()
    await provider.setup()
    request = FetchRequest(url="https://httpbin.org/get")

    with patch.object(provider._client, "request", AsyncMock()) as mock_request:
        mock_request.return_value = httpx.Response(
            200,
            content=b"ok",
            headers={"content-type": "text/plain"},
            request=httpx.Request("GET", "https://httpbin.org/get"),
        )
        result = await provider.fetch(request)
        assert result.status_code == 200
        assert result.content == b"ok"
        assert result.content_type == "text/plain"

    await provider.teardown()


@pytest.mark.asyncio
async def test_fetch_auto_setup():
    provider = HTTPXProvider()
    request = FetchRequest(url="https://example.com")

    # Combine patches into one with statement
    with (
        patch.object(provider, "setup", AsyncMock()) as mock_setup,
        patch.object(provider._client, "request", AsyncMock()) as mock_request,
    ):
        mock_request.return_value = httpx.Response(
            200,
            content=b"ok",
            request=httpx.Request("GET", "https://example.com"),
        )
        await provider.fetch(request)
        mock_setup.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_httpx_error():
    provider = HTTPXProvider()
    await provider.setup()
    request = FetchRequest(url="https://example.com")

    with patch.object(
        provider._client,
        "request",
        AsyncMock(side_effect=httpx.ConnectTimeout("timeout")),
    ):
        with pytest.raises(FetchError) as exc:
            await provider.fetch(request)
        assert "timeout" in str(exc.value)
        assert exc.value.cause is not None
        assert isinstance(exc.value.cause, httpx.ConnectTimeout)

    await provider.teardown()


@pytest.mark.asyncio
async def test_fetch_with_custom_timeout():
    provider = HTTPXProvider()
    await provider.setup()
    request = FetchRequest(url="https://example.com", timeout=5.0)

    with patch.object(provider._client, "request", AsyncMock()) as mock_request:
        mock_request.return_value = httpx.Response(
            200,
            content=b"ok",
            request=httpx.Request("GET", "https://example.com"),
        )
        await provider.fetch(request)
        _, kwargs = mock_request.call_args
        assert kwargs["timeout"] == 5.0

    await provider.teardown()
