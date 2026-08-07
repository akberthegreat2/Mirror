"""Typed models for the Deduplication capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class DedupDocument:
    """A text document candidate for deduplication."""

    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class DeduplicatedDocument:
    """A canonical document retained after deduplication."""

    document_id: str
    text: str
    fingerprint: str
    duplicate_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class DedupDecision:
    """A deduplication decision for one duplicate document."""

    duplicate_document_id: str
    canonical_document_id: str
    fingerprint: str
    reason: str = "duplicate"


class DedupRequest(BaseModel):
    """Input for a deduplication run."""

    documents: list[DedupDocument] = Field(default_factory=list)


class DedupResult(BaseModel):
    """Output of a deduplication run."""

    documents: list[DeduplicatedDocument] = Field(default_factory=list)
    duplicates: list[DedupDecision] = Field(default_factory=list)
    removed_count: int = 0
