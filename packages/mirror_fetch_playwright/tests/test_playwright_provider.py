"""Tests for the Playwright-style fetch provider."""

from __future__ import annotations

from types import SimpleNamespace
from urllib import error as urllib_error

import pytest
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest
from mirror_fetch.protocol import Fetch
from mirror_fetch_playwright.provider import PlaywrightProvider
from mirror_fetch_playwright.settings import PlaywrightSettings


class _FakeHeaders(dict):
    def get_content_charset(self, default: str = "utf-8") -> str:
        return self.get("charset", default)


class _FakeResponse:
    def __init__(self, url: str = "https://example.com") -> None:
        self.url = url
        self.status = 200
        self.headers = _FakeHeaders({"Content-Type": "text/plain; charset=utf-8", "Content-Length": "2"})
        self._closed = False

    def read(self) -> bytes:
        return b"ok"

    def close(self) -> None:
        self._closed = True


@pytest.mark.asyncio
async def test_descriptor_protocol() -> None:
    """The provider must satisfy the Fetch protocol."""
    provider = PlaywrightProvider()
    assert isinstance(provider, Fetch)


@pytest.mark.asyncio
async def test_fetch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """The provider should return a typed fetch result."""
    provider = PlaywrightProvider(PlaywrightSettings(user_agent="Mirror-Test/1.0"))

    def fake_open(request: FetchRequest, timeout: float) -> _FakeResponse:
        assert timeout == 30.0
        assert request.headers == {}
        return _FakeResponse(str(request.url))

    monkeypatch.setattr(provider, "_open", fake_open)

    result = await provider.fetch(FetchRequest(url="https://example.com"))
    assert result.url == "https://example.com/"
    assert result.status_code == 200
    assert result.content == b"ok"
    assert result.content_type == "text/plain; charset=utf-8"
    assert result.content_length == 2


@pytest.mark.asyncio
async def test_fetch_error_translation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Backend failures should become FetchError instances."""
    provider = PlaywrightProvider()

    def fake_open(request: FetchRequest, timeout: float) -> _FakeResponse:
        raise urllib_error.URLError("boom")

    monkeypatch.setattr(provider, "_open", fake_open)

    with pytest.raises(FetchError) as exc:
        await provider.fetch(FetchRequest(url="https://example.com"))
    assert "boom" in str(exc.value)
    assert exc.value.cause is not None


@pytest.mark.asyncio
async def test_lifecycle_idempotent() -> None:
    """The provider lifecycle should be idempotent."""
    provider = PlaywrightProvider()
    await provider.setup()
    await provider.setup()
    await provider.teardown()
    await provider.teardown()
