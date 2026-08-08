from __future__ import annotations

import importlib.util

import pytest
from mirror_crawl.models import CrawlRequest
from mirror_crawl_scrapy.provider import ScrapyCrawlProvider, provider


def test_manifest_uses_scrapy_provider() -> None:
    assert provider.name == "scrapy"
    assert provider.capability == "crawl"


@pytest.mark.integration
@pytest.mark.skipif(
    importlib.util.find_spec("scrapy") is None, reason="Scrapy is not installed"
)
def test_scrapy_provider_is_importable() -> None:
    assert ScrapyCrawlProvider()._settings is not None
    assert CrawlRequest(url="https://example.com").max_depth == 1
