"""Crawl service orchestration built on a resolved Fetch protocol implementation."""

from __future__ import annotations

import hashlib
import logging
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from mirror_core.exceptions import ExecutionError
from mirror_core.storage import BlobStore, MetadataRecord, MetadataStore
from mirror_crawl.models import CrawlRecord, CrawlRequest, CrawlResult
from mirror_fetch.models import FetchRequest, FetchResult
from mirror_fetch.protocol import Fetch
from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class CrawlService:
    """Orchestrate a crawl using an injected Fetch protocol implementation."""

    def __init__(self, fetch: Fetch) -> None:
        self._fetch = fetch

    async def crawl(
        self,
        request: CrawlRequest,
        *,
        metadata_store: MetadataStore | None = None,
        blob_store: BlobStore | None = None,
    ) -> CrawlResult:
        return await crawl_site(
            self._fetch,
            request,
            metadata_store=metadata_store,
            blob_store=blob_store,
        )


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.title: str | None = None
        self._capture_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.links.append(value)
        if tag.lower() == "title":
            self._capture_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._capture_title = False

    def handle_data(self, data: str) -> None:
        if self._capture_title and self.title is None:
            stripped = data.strip()
            if stripped:
                self.title = stripped


async def crawl_site(
    fetcher: Fetch,
    request: CrawlRequest,
    *,
    metadata_store: MetadataStore | None = None,
    blob_store: BlobStore | None = None,
) -> CrawlResult:
    seed = str(request.url)
    parsed_seed = urlparse(seed)
    queue: list[tuple[str, int, str | None]] = [(seed, 0, None)]
    seen: set[str] = {seed}
    discovered: list[CrawlRecord] = []
    visited: list[str] = []
    stored_pages = 0
    stored_urls = 0

    while queue and len(visited) < request.max_pages:
        current_url, depth, parent_url = queue.pop(0)
        if current_url in visited:
            continue
        visited.append(current_url)
        try:
            result = await fetcher.fetch(FetchRequest(url=HttpUrl(current_url)))
        except Exception as exc:  # noqa: BLE001 - surfaced in the result list
            logger.debug(
                "crawl fetch failed", extra={"url": current_url, "error": str(exc)}
            )
            continue

        title, links = _parse_html(result)
        blob_key = None
        if (
            request.store_pages
            and blob_store is not None
            and _is_html(result.content_type)
        ):
            blob_key = _blob_key(request, current_url, result)
            blob_store.put_bytes(blob_key, result.content)
            stored_pages += 1

        record = CrawlRecord(
            url=current_url,
            depth=depth,
            parent_url=parent_url,
            status_code=result.status_code,
            title=title,
            content_type=result.content_type,
            blob_key=blob_key,
        )
        discovered.append(record)

        if request.persist_discovered_urls and metadata_store is not None:
            metadata_store.put(
                MetadataRecord(
                    namespace=request.metadata_namespace,
                    key=current_url,
                    payload={
                        "depth": depth,
                        "parent_url": parent_url,
                        "status_code": result.status_code,
                        "content_type": result.content_type,
                        "blob_key": blob_key,
                    },
                )
            )
            stored_urls += 1

        if depth >= request.max_depth:
            continue

        for link in links:
            absolute = urljoin(current_url, link)
            if absolute in seen:
                continue
            if (
                request.same_host_only
                and urlparse(absolute).netloc != parsed_seed.netloc
            ):
                continue
            seen.add(absolute)
            queue.append((absolute, depth + 1, current_url))

    return CrawlResult(
        seed_url=seed,
        discovered_urls=discovered,
        visited_urls=visited,
        stored_urls=stored_urls,
        stored_pages=stored_pages,
    )


def _parse_html(result: FetchResult) -> tuple[str | None, list[str]]:
    if result.content_type is not None and "html" not in result.content_type.lower():
        return None, []
    parser = _LinkExtractor()
    try:
        parser.feed(result.content.decode(result.encoding or "utf-8", errors="replace"))
    except Exception as exc:  # pragma: no cover - parsing failures should be rare
        raise ExecutionError("Unable to parse HTML during crawl", cause=exc) from exc
    return parser.title, parser.links


def _blob_key(request: CrawlRequest, url: str, result: FetchResult) -> str:
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    extension = ".html" if _is_html(result.content_type) else ".bin"
    host = urlparse(str(request.url)).netloc or "crawl"
    return f"{request.blob_namespace}/{host}/{digest}{extension}"


def _is_html(content_type: str | None) -> bool:
    return content_type is not None and "html" in content_type.lower()
