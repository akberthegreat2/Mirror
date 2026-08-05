"""Local crawl provider implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.registry import ProviderConfig
from mirror_core.storage import BlobStore, MetadataStore
from mirror_fetch.protocol import Fetch
from mirror_fetch_httpx.provider import HTTPXProvider
from mirror_fetch_httpx.settings import HTTPXSettings
from mirror_fetch_playwright.provider import PlaywrightProvider
from mirror_fetch_playwright.settings import PlaywrightSettings

from mirror_crawl.models import CrawlRequest, CrawlResult, CrawlSettings
from mirror_crawl.runner import crawl_site


class LocalCrawlProvider(AsyncLifecycle):
    """Crawl provider that composes an underlying fetch backend."""

    def __init__(self, settings: CrawlSettings | None = None) -> None:
        self._settings = settings or CrawlSettings()
        self._fetch: Fetch | None = None
        self._started = False

    async def setup(self) -> None:
        if self._fetch is None:
            self._fetch = self._build_fetcher()
        lifecycle = self._fetch if isinstance(self._fetch, AsyncLifecycle) else None
        if lifecycle is not None:
            await lifecycle.setup()
        self._started = True

    async def teardown(self) -> None:
        lifecycle = self._fetch if isinstance(self._fetch, AsyncLifecycle) else None
        if lifecycle is not None:
            await lifecycle.teardown()
        self._started = False

    async def crawl(self, request: CrawlRequest) -> CrawlResult:
        if not self._started:
            await self.setup()
        assert self._fetch is not None
        return await crawl_site(self._fetch, request)

    def _build_fetcher(self) -> Fetch:
        if self._settings.fetch_provider == "httpx":
            fetch_settings = HTTPXSettings.model_validate(self._settings.fetch_settings)
            return HTTPXProvider(fetch_settings)
        fetch_settings = PlaywrightSettings.model_validate(self._settings.fetch_settings)
        return PlaywrightProvider(fetch_settings)


provider = ProviderConfig(
    name="local",
    capability="crawl",
    capability_api="~=1.0",
    factory="mirror_crawl.provider:LocalCrawlProvider",
    settings_model="mirror_crawl.models:CrawlSettings",
    features=["crawl", "persist", "storage"],
    priority=10,
    metadata={"description": "Local crawl provider composed from Mirror Fetch."},
)
