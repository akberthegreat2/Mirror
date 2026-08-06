"""Crawler runner – adapts a crawl provider to the capability contract."""

from __future__ import annotations

from mirror_crawl.models import CrawlRequest, CrawlResult
from mirror_crawl.protocol import Crawl


async def crawl_site(
    provider: Crawl,
    request: CrawlRequest,
    settings: object | None = None,
    signal_bus: object | None = None,
    step_id: str | None = None,
    metadata_store: object | None = None,
    blob_store: object | None = None,
) -> CrawlResult:
    del settings, signal_bus, step_id, metadata_store, blob_store
    return await provider.crawl(request)
