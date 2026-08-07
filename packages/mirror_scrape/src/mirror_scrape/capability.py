"""Capability descriptors for the scrape capability."""

from mirror_core.extensions.models import CapabilityManifest

from .models import ScrapeRequest, ScrapeResult
from .protocol import Scrape
from .settings import ScrapeSettings

capability = CapabilityManifest(
    name="scrape",
    api_version="1.0.0",
    protocol=Scrape,
    request_model=ScrapeRequest,
    result_model=ScrapeResult,
    settings_model=ScrapeSettings,
    runner="mirror_scrape.runner:scrape_step",
    metadata={"summary": "Scrape capability"},
)
