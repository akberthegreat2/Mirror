"""Tests for the crawl capability and local provider."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Callable

import pytest
from mirror_core.storage import InMemoryBlobStore, InMemoryMetadataStore
from mirror_crawl.models import CrawlRequest, CrawlSettings
from mirror_crawl.provider import LocalCrawlProvider
from mirror_crawl.runner import crawl_site
from mirror_fetch.models import FetchRequest, FetchResult


class _FakeFetchProvider:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    async def fetch(self, request: FetchRequest) -> FetchResult:
        url = str(request.url)
        body = self.pages[url].encode("utf-8")
        return FetchResult(
            url=url,
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=body,
            encoding="utf-8",
            content_type="text/html; charset=utf-8",
            content_length=len(body),
            fetch_duration=0.0,
            timestamp="2026-08-05T00:00:00+00:00",
        )


@asynccontextmanager
async def _local_http_server() -> Callable[[str], str]:
    pages = {
        "/": (
            "<html><head><title>Home</title></head><body>"
            '<a href="/about">About</a>'
            "</body></html>"
        ),
        "/about": (
            "<html><head><title>About</title></head><body>"
            '<a href="/">Home</a>'
            "</body></html>"
        ),
    }

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request_line = await reader.readline()
        path = request_line.decode("ascii", errors="ignore").split(" ")[1]
        while True:
            line = await reader.readline()
            if line in {b"\r\n", b"\n", b""}:
                break
        body = pages.get(path, "<html><body>missing</body></html>")
        payload = body.encode("utf-8")
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            + f"Content-Length: {len(payload)}\r\n".encode("ascii")
            + b"Connection: close\r\n\r\n"
            + payload
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    base = f"http://{host}:{port}"
    try:
        yield lambda path: f"{base}{path}"
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_crawl_persists_discovered_urls() -> None:
    """The crawl runner should save discovered URLs and page blobs on demand."""
    provider = _FakeFetchProvider(
        {
            "https://example.com/": (
                "<html><head><title>Home</title></head><body>"
                '<a href="/about">About</a>'
                "</body></html>"
            ),
            "https://example.com/about": (
                "<html><head><title>About</title></head><body>"
                '<a href="/">Home</a>'
                "</body></html>"
            ),
        }
    )
    metadata_store = InMemoryMetadataStore()
    blob_store = InMemoryBlobStore()
    result = await crawl_site(
        provider,  # type: ignore[arg-type]
        CrawlRequest(url="https://example.com", max_depth=1, max_pages=5),
        metadata_store=metadata_store,
        blob_store=blob_store,
    )
    assert result.seed_url == "https://example.com/"
    assert result.stored_urls == 2
    assert result.stored_pages == 2
    assert metadata_store.get("crawl.urls", "https://example.com/") is not None
    assert metadata_store.get("crawl.urls", "https://example.com/about") is not None
    assert any(record.url == "https://example.com/about" for record in result.discovered_urls)
    assert len(result.discovered_urls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("fetch_provider", ["httpx", "playwright"])
async def test_local_crawl_provider_can_swap_fetch_backend(fetch_provider: str) -> None:
    """The crawl provider should work with either HTTPX or Playwright fetch backends."""
    async with _local_http_server() as make_url:
        provider = LocalCrawlProvider(CrawlSettings(fetch_provider=fetch_provider))
        result = await provider.crawl(CrawlRequest(url=make_url("/"), max_depth=1, max_pages=5))
        assert result.seed_url.startswith("http://127.0.0.1:")
        assert {record.url for record in result.discovered_urls} >= {make_url("/"), make_url("/about")}
