"""HTTPX fetch provider implementation."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from mirror_core.lifecycle import AsyncLifecycle
from mirror_fetch.exceptions import FetchError
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch

from mirror_fetch_httpx.settings import HTTPXSettings


class HTTPXProvider(AsyncLifecycle, Fetch):
    """Fetch provider using HTTPX."""

    def __init__(self, settings: HTTPXSettings | None = None) -> None:
        self._settings = settings or HTTPXSettings()
        self._client: httpx.AsyncClient | None = None  # type: ignore[no-any-unimported]

    async def setup(self) -> None:
        if self._client is None:
            timeout = httpx.Timeout(
                timeout=self._settings.default_timeout,
                connect=self._settings.default_timeout,
                read=self._settings.default_timeout,
                write=self._settings.default_timeout,
            )
            self._client = httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=self._settings.follow_redirects,
                max_redirects=self._settings.max_redirects,
                headers={"User-Agent": self._settings.user_agent},
            )

    async def teardown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch(self, request: FetchRequest) -> FetchResult:
        if self._client is None:
            await self.setup()
        assert self._client is not None

        start_time = datetime.now(timezone.utc)

        try:
            response = await self._client.request(
                method=request.method,
                url=str(request.url),
                headers=request.headers,
                content=request.body,
                timeout=request.timeout or self._settings.default_timeout,
            )
        except httpx.HTTPError as exc:
            raise FetchError(
                f"Failed to fetch {request.url}: {exc}",
                details={"url": str(request.url), "error_type": type(exc).__name__},
                cause=exc,
            ) from exc

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        return FetchResult(
            url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            encoding=response.encoding or "utf-8",
            content_type=response.headers.get("content-type"),
            content_length=response.headers.get("content-length"),
            fetch_duration=duration,
            timestamp=start_time.isoformat(timespec="seconds"),
        )
