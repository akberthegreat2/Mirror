"""Typed models for the Enrichment capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class EnrichmentDocument:
    """A raw text document to enrich."""

    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class EnrichmentStatistics:
    """Stable statistics derived from one document."""

    character_count: int
    line_count: int
    sentence_count: int
    word_count: int
    unique_word_count: int
    keyword_count: int
    url_count: int


@dataclass(slots=True, frozen=True)
class EnrichedDocument:
    """A deterministic enrichment snapshot for one document."""

    document_id: str
    original_text: str
    enriched_text: str
    summary: str
    keywords: tuple[str, ...]
    urls: tuple[str, ...]
    statistics: EnrichmentStatistics
    metadata: dict[str, Any] = field(default_factory=dict)


class EnrichmentRequest(BaseModel):
    """Input for an enrichment run."""

    documents: list[EnrichmentDocument] = Field(default_factory=list)


class EnrichmentResult(BaseModel):
    """Output of an enrichment run."""

    documents: list[EnrichedDocument] = Field(default_factory=list)
