"""Tests for the real Playwright fetch provider."""

from __future__ import annotations

from typing import Any

import pytest
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest
from mirror_fetch.protocol import Fetch
from mirror_fetch_playwright.provider import PlaywrightProvider
from mirror_fetch_playwright.settings import PlaywrightSettings


class FakeResponse:
    status = 200

    async def all_headers(self) -> dict[str, str]:
        return {"content-type": "text/html"}


class FakePage:
    url = "https://example.com/"

    async def goto(self, *args: Any, **kwargs: Any) -> FakeResponse:
        return FakeResponse()

    async def content(self) -> str:
        return "<html>ok</html>"


class FakeContext:
    closed = False

    async def new_page(self) -> FakePage:
        return FakePage()

    async def close(self) -> None:
        self.closed = True


class FakeBrowser:
    closed = False

    async def new_context(self, **kwargs: Any) -> FakeContext:
        return FakeContext()

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_descriptor_protocol() -> None:
    assert isinstance(PlaywrightProvider(), Fetch)


@pytest.mark.asyncio
async def test_fetch_success() -> None:
    browser = FakeBrowser()

    async def launch(settings: PlaywrightSettings) -> FakeBrowser:
        return browser

    provider = PlaywrightProvider(launcher=launch)
    await provider.setup()
    result = await provider.fetch(FetchRequest(url="https://example.com"))
    assert result.status_code == 200
    assert result.content == b"<html>ok</html>"
    await provider.teardown()
    assert browser.closed is True


@pytest.mark.asyncio
async def test_fetch_requires_setup() -> None:
    provider = PlaywrightProvider()
    with pytest.raises(FetchError, match="not initialized"):
        await provider.fetch(FetchRequest(url="https://example.com"))


@pytest.mark.asyncio
async def test_lifecycle_idempotent() -> None:
    browser = FakeBrowser()
    launches = 0

    async def launch(settings: PlaywrightSettings) -> FakeBrowser:
        nonlocal launches
        launches += 1
        return browser

    provider = PlaywrightProvider(launcher=launch)
    await provider.setup()
    await provider.setup()
    assert launches == 1
    await provider.teardown()
    await provider.teardown()
