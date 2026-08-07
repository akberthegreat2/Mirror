"""Typed models for the Retrieval capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class RetrievalHit:
    """A ranked retrieval match."""

    record_id: str
    document_id: str
    chunk_id: str | None
    score: float
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    score_details: dict[str, Any] = field(default_factory=dict)


class RetrievalRequest(BaseModel):
    """Input for a retrieval run."""

    query: str = Field(min_length=1)
    namespace: str | None = Field(default=None, min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=100)
    filters: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Output of a retrieval run."""

    query: str
    namespace: str
    matches: list[RetrievalHit] = Field(default_factory=list)
    evaluation: dict[str, Any] = Field(default_factory=dict)
