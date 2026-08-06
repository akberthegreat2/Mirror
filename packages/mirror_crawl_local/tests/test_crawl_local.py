"""Tests for the local crawl provider package."""

from __future__ import annotations

import pytest
from mirror_crawl.models import CrawlRequest, CrawlSettings
from mirror_crawl_local.provider import LocalCrawlProvider
from mirror_fetch.models import FetchRequest, FetchResult


class _FakeFetchProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def fetch(self, request: FetchRequest) -> FetchResult:
        self.calls.append(str(request.url))
        return FetchResult(
            url=str(request.url),
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><head><title>Home</title></head><body></body></html>",
            encoding="utf-8",
            content_type="text/html; charset=utf-8",
            content_length=0,
            fetch_duration=0.0,
            timestamp="2026-08-05T00:00:00+00:00",
        )


@pytest.mark.asyncio
async def test_local_provider_crawls_via_injected_fetcher() -> None:
    fetch = _FakeFetchProvider()
    provider = LocalCrawlProvider(CrawlSettings(), fetch=fetch)
    result = await provider.crawl(CrawlRequest(url="https://example.com"))
    assert result.seed_url == "https://example.com/"
    assert fetch.calls == ["https://example.com/"]


class _LifecycleFetchProvider(_FakeFetchProvider):
    def __init__(self) -> None:
        super().__init__()
        self.setup_calls = 0
        self.teardown_calls = 0

    async def setup(self) -> None:
        self.setup_calls += 1

    async def teardown(self) -> None:
        self.teardown_calls += 1


@pytest.mark.asyncio
async def test_local_provider_does_not_own_dependency_lifecycle() -> None:
    fetch = _LifecycleFetchProvider()
    provider = LocalCrawlProvider(CrawlSettings(), fetch=fetch)
    await provider.crawl(CrawlRequest(url="https://example.com"))
    assert fetch.setup_calls == 0
    assert fetch.teardown_calls == 0
