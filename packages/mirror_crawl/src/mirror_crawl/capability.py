"""Crawl capability descriptor."""

from mirror_core.registry import CapabilityConfig

from mirror_crawl.models import CrawlRequest, CrawlResult, CrawlSettings
from mirror_crawl.protocol import Crawl

capability = CapabilityConfig(
    name="crawl",
    api_version="1.0",
    protocol=Crawl,
    request_model=CrawlRequest,
    result_model=CrawlResult,
    settings_model=CrawlSettings,
    runner="mirror_crawl.runner:crawl_site",
    input_ports={},
    output_ports={"result": CrawlResult},
    required_capabilities=["fetch"],
    signals=[
        "crawl.started",
        "crawl.page.discovered",
        "crawl.page.stored",
        "crawl.finished",
    ],
    metadata={"description": "Crawl a website, persist discovered URLs, and store pages."},
)
