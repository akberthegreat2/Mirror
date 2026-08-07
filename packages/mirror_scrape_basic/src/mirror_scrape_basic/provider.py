"""Basic Scrape provider."""

from __future__ import annotations

from mirror_core.extensions.models import ProviderManifest
from mirror_scrape.models import ScrapeRequest, ScrapeResult
from mirror_scrape.protocol import Scrape

from .scraper import Scraper


class BasicScrapeProvider(Scrape):
    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        return ScrapeResult(document=Scraper().scrape(request.html, url=request.url))


provider = ProviderManifest(
    name="basic",
    capability="scrape",
    capability_api="~=1.0",
    factory="mirror_scrape_basic.provider:BasicScrapeProvider",
    metadata={"description": "Basic HTML scraping provider."},
)
