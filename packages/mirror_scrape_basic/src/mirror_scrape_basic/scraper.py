"""HTML scraping helpers."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

from mirror_scrape.models import ScrapedDocument


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.title: str | None = None
        self._capture_title = False
        self._texts: list[str] = []
        self._headings: list[str] = []
        self._in_heading: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.links.append(value)
        if tag.lower() == "title":
            self._capture_title = True
        if tag.lower() in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._in_heading = tag.lower()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._capture_title = False
        if tag.lower() in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._in_heading = None

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if not stripped:
            return
        if self._capture_title and self.title is None:
            self.title = stripped
        if self._in_heading is not None:
            self._headings.append(stripped)
        self._texts.append(stripped)


@dataclass(slots=True)
class Scraper:
    def scrape(self, html: str, *, url: str | None = None) -> ScrapedDocument:
        extractor = _Extractor()
        extractor.feed(html)
        return ScrapedDocument(
            url=url,
            title=extractor.title,
            text=" ".join(extractor._texts),
            links=tuple(extractor.links),
            meta={},
            headings=tuple(extractor._headings),
        )
