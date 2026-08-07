"""Typed scrape-domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class ScrapedDocument:
    """Structured document extracted from HTML."""

    url: str | None
    title: str | None
    text: str
    links: tuple[str, ...]
    meta: dict[str, str]
    headings: tuple[str, ...]
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ScrapeRequest(BaseModel):
    """Input for an HTML scraping operation."""

    html: str = Field(min_length=1)
    url: str | None = None


class ScrapeResult(BaseModel):
    """Output of an HTML scraping operation."""

    document: ScrapedDocument
