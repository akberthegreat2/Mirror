"""Scrape runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import ScrapeError
from .models import ScrapeRequest, ScrapeResult
from .protocol import Scrape


async def scrape_step(provider: Scrape, request: ScrapeRequest) -> ScrapeResult:
    """Adapt a Scrape provider to the capability runner contract."""
    try:
        return await provider.scrape(request)
    except ScrapeError:
        raise
    except Exception as exc:
        raise ScrapeError("Failed to scrape document", cause=exc) from exc
