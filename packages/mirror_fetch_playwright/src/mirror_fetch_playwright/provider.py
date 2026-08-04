"""Playwright browser provider for the Fetch capability."""

from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Awaitable, Callable
from typing import Any

from mirror_core.lifecycle import AsyncLifecycle
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch

from mirror_fetch_playwright.settings import PlaywrightSettings


class PlaywrightProvider(AsyncLifecycle, Fetch):
    """Fetch rendered browser content using Playwright."""

    def __init__(self, settings: PlaywrightSettings | None = None, *, launcher: Callable[[PlaywrightSettings], Awaitable[Any]] | None = None) -> None:
        self._settings = settings or PlaywrightSettings()
        self._launcher = launcher
        self._playwright: Any = None
        self._browser: Any = None

    async def setup(self) -> None:
        if self._browser is not None:
            return
        if self._launcher is not None:
            self._browser = await self._launcher(self._settings)
            return
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise FetchError("Playwright provider requires 'playwright'; install mirror-fetch-playwright") from exc
        self._playwright = await async_playwright().start()
        browser_type = getattr(self._playwright, self._settings.browser)
        try:
            self._browser = await browser_type.launch(headless=self._settings.headless)
        except Exception as exc:
            await self._playwright.stop()
            self._playwright = None
            raise FetchError("Playwright browser executable is unavailable; run 'playwright install'", cause=exc) from exc

    async def teardown(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def fetch(self, request: FetchRequest) -> FetchResult:
        if self._browser is None:
            raise FetchError("Playwright provider is not initialized; call setup() first")
        started_at = datetime.now(timezone.utc)
        context = await self._browser.new_context(user_agent=self._settings.user_agent,
            viewport={"width": self._settings.viewport_width, "height": self._settings.viewport_height})
        page = await context.new_page()
        try:
            response = await page.goto(str(request.url), wait_until=self._settings.wait_until,
                timeout=int((request.timeout or self._settings.default_timeout) * 1000))
            content = (await page.content()).encode("utf-8")
            headers = await response.all_headers() if response is not None else {}
            status = response.status if response is not None else 200
            return FetchResult(url=page.url, status_code=status, headers=headers, content=content,
                encoding="utf-8", content_type=headers.get("content-type"), content_length=len(content),
                fetch_duration=(datetime.now(timezone.utc)-started_at).total_seconds(),
                timestamp=started_at.isoformat(timespec="seconds"))
        except Exception as exc:
            raise FetchError(f"Failed to fetch {request.url}: {exc}", details={"url": str(request.url), "error_type": type(exc).__name__}, cause=exc) from exc
        finally:
            await context.close()
