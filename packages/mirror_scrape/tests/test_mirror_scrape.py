"""Tests for the scrape capability package."""

from __future__ import annotations

import pytest
from mirror_scrape import ScrapeRequest, ScrapeResult, capability, scrape_step
from mirror_scrape_basic import BasicScrapeProvider, Scraper


class FakeScrapeProvider:
    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        return ScrapeResult(document=Scraper().scrape(request.html, url=request.url))


def test_capability_descriptor() -> None:
    assert capability.name == "scrape"
    assert capability.request_model == ScrapeRequest
    assert capability.result_model == ScrapeResult
    assert capability.runner == "mirror_scrape.runner:scrape_step"


def test_scraper_extracts_text() -> None:
    document = Scraper().scrape(
        "<html><head><title>Hello</title></head><body><a href='/x'>X</a></body></html>",
        url="https://example.com",
    )
    assert document.title == "Hello"
    assert document.links == ("/x",)
    assert document.text


@pytest.mark.asyncio
async def test_scrape_step() -> None:
    result = await scrape_step(
        FakeScrapeProvider(), ScrapeRequest(html="<html><body>Hello</body></html>")
    )
    assert result.document.text


@pytest.mark.asyncio
async def test_basic_scrape_provider() -> None:
    result = await BasicScrapeProvider().scrape(
        ScrapeRequest(html="<html><body>Hello</body></html>")
    )
    assert result.document.text
