"""Crawl capability descriptor."""

from mirror_core.extensions.models import CapabilityManifest, Dependency

from mirror_crawl.models import CrawlRequest, CrawlResult, CrawlSettings
from mirror_crawl.protocol import Crawl

capability = CapabilityManifest(
    name="crawl",
    api_version="1.0",
    protocol=Crawl,
    request_model=CrawlRequest,
    result_model=CrawlResult,
    settings_model=CrawlSettings,
    runner="mirror_crawl.runner:crawl_site",
    input_ports={},
    output_ports={"result": CrawlResult},
    dependencies=[Dependency(name="fetch", version="~=1.0")],
    metadata={"description": "Crawl a website and persist discovered URLs."},
)
