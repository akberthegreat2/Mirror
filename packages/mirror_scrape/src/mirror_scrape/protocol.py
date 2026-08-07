"""Scrape capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import ScrapeRequest, ScrapeResult


@runtime_checkable
class Scrape(Protocol):
    """Protocol for scrape providers."""

    async def scrape(self, request: ScrapeRequest) -> ScrapeResult: ...
