"""Typed request, result, and settings models for crawl workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CrawlRequest(BaseModel):
    """Input for a crawl operation."""

    url: HttpUrl
    max_depth: int = Field(default=1, ge=0, le=10)
    max_pages: int = Field(default=20, ge=1, le=10_000)
    same_host_only: bool = True
    persist_discovered_urls: bool = True
    store_pages: bool = True
    metadata_namespace: str = "crawl.urls"
    blob_namespace: str = "crawl.pages"
    fetch_provider: str = "httpx"
    fetch_settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata_namespace", "blob_namespace", mode="after")
    @classmethod
    def _strip_namespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("namespace cannot be empty")
        return value.strip()


class CrawlRecord(BaseModel):
    """One discovered URL and its crawl metadata."""

    model_config = ConfigDict(frozen=True)

    url: str
    depth: int
    parent_url: str | None = None
    status_code: int | None = None
    title: str | None = None
    content_type: str | None = None
    blob_key: str | None = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CrawlResult(BaseModel):
    """Terminal crawl summary."""

    model_config = ConfigDict(frozen=True)

    seed_url: str
    discovered_urls: list[CrawlRecord] = Field(default_factory=list)
    visited_urls: list[str] = Field(default_factory=list)
    stored_urls: int = 0
    stored_pages: int = 0


class CrawlSettings(BaseModel):
    """Runtime settings for the local crawl provider."""

    model_config = ConfigDict(frozen=True)

    fetch_provider: Literal["httpx", "playwright"] = "httpx"
    fetch_settings: dict[str, Any] = Field(default_factory=dict)
    user_agent: str = "Mirror Crawl/0.1"
    extract_titles: bool = True
