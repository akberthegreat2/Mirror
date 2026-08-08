import pytest
from mirror_scrape.models import ScrapeRequest, ScrapeResult
from mirror_scrape_basic import BasicScrapeProvider, Scraper


def test_scraper_extracts_text() -> None:
    document = Scraper().scrape(
        "<html><head><title>Hello</title></head><body><a href='/x'>X</a></body></html>",
        url="https://example.com",
    )
    assert document.title == "Hello"
    assert document.links == ("/x",)
    assert document.text


@pytest.mark.asyncio
async def test_basic_scrape_provider_works() -> None:
    result = await BasicScrapeProvider().scrape(ScrapeRequest(html="<html><body>Hello</body></html>"))
    assert isinstance(result, ScrapeResult)
    assert result.document.text
