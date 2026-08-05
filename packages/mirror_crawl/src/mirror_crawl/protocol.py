"""Crawl capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mirror_crawl.models import CrawlRequest, CrawlResult


@runtime_checkable
class Crawl(Protocol):
    """Protocol for crawl providers."""

    async def crawl(self, request: CrawlRequest) -> CrawlResult:
        """Crawl a seed URL and return typed results."""
        ...
