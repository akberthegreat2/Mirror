"""Typed models for the Chunking capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class ChunkDocument:
    """A text document ready for chunking."""

    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class Chunk:
    """A single text chunk with provenance."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    start_token: int
    end_token: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ChunkRequest(BaseModel):
    """Input for a chunking run."""

    documents: list[ChunkDocument] = Field(default_factory=list)


class ChunkResult(BaseModel):
    """Output of a chunking run."""

    chunks: list[Chunk] = Field(default_factory=list)
