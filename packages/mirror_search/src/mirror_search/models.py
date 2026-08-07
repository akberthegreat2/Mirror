"""Typed search-domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class SearchHit:
    """A single ranked search hit."""

    document_id: str
    score: float
    title: str | None = None
    url: str | None = None
    snippet: str | None = None


class SearchRequest(BaseModel):
    """Input for a search operation."""

    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Output of a search operation."""

    query: str
    hits: list[SearchHit] = Field(default_factory=list)
    total: int = 0
    index_name: str = "memory"
    metadata: dict[str, Any] = Field(default_factory=dict)
