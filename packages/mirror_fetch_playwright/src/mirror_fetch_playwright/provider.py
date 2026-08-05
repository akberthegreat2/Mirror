"""Playwright-style fetch provider implementation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from http.client import HTTPResponse
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from mirror_core.lifecycle import AsyncLifecycle
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch

from mirror_fetch_playwright.settings import PlaywrightSettings


class PlaywrightProvider(AsyncLifecycle, Fetch):
    """Fetch provider with Playwright-compatible settings and a lightweight backend."""

    def __init__(self, settings: PlaywrightSettings | None = None) -> None:
        """Create a new provider instance.

        Args:
            settings: Optional provider settings.
        """
        self._settings = settings or PlaywrightSettings()
        self._started = False

    async def setup(self) -> None:
        """Mark the provider as ready."""
        self._started = True

    async def teardown(self) -> None:
        """Release provider state."""
        self._started = False

    async def fetch(self, request: FetchRequest) -> FetchResult:
        """Fetch a URL and return a typed Mirror result.

        Args:
            request: Typed fetch request.

        Returns:
            A typed fetch result.

        Raises:
            FetchError: If the request cannot be completed.
        """
        if not self._started:
            await self.setup()

        started_at = datetime.now(timezone.utc)
        timeout = request.timeout or self._settings.default_timeout
        try:
            response = await asyncio.to_thread(self._open, request, timeout)
        except (urllib_error.URLError, OSError, TimeoutError, ValueError) as exc:
            raise FetchError(
                f"Failed to fetch {request.url}: {exc}",
                details={"url": str(request.url), "error_type": type(exc).__name__},
                cause=exc,
            ) from exc

        try:
            return self._build_result(request, response, started_at)
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()

    def _open(self, request: FetchRequest, timeout: float) -> Any:
        """Open a request synchronously inside a worker thread."""
        headers = {"User-Agent": self._settings.user_agent, **request.headers}
        url_request = urllib_request.Request(
            url=str(request.url),
            data=request.body,
            headers=headers,
            method=request.method,
        )
        return urllib_request.urlopen(url_request, timeout=timeout)

    @staticmethod
    def _build_result(
        request: FetchRequest,
        response: HTTPResponse | Any,
        started_at: datetime,
    ) -> FetchResult:
        """Convert a backend response into the canonical Mirror fetch result."""
        headers = dict(getattr(response, "headers", {}).items())
        body = response.read()
        if not isinstance(body, bytes):
            body = bytes(body)
        encoding = "utf-8"
        content_type = headers.get("Content-Type") or headers.get("content-type")
        content_length = headers.get("Content-Length") or headers.get("content-length")
        header_object = getattr(response, "headers", None)
        if header_object is not None:
            charset = getattr(header_object, "get_content_charset", None)
            if callable(charset):
                encoding = charset("utf-8") or "utf-8"
        return FetchResult(
            url=str(getattr(response, "url", request.url)),
            status_code=int(getattr(response, "status", getattr(response, "code", 200))),
            headers=headers,
            content=body,
            encoding=encoding,
            content_type=content_type,
            content_length=int(content_length) if content_length and str(content_length).isdigit() else None,
            fetch_duration=(datetime.now(timezone.utc) - started_at).total_seconds(),
            timestamp=started_at.isoformat(timespec="seconds"),
        )
