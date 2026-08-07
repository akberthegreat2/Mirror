"""Typed models for the Embedding capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class EmbeddingInput:
    """A single text input to embed."""

    item_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class EmbeddingVector:
    """A single embedded vector with provenance."""

    item_id: str
    values: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingRequest(BaseModel):
    """Input for an embedding run."""

    items: list[EmbeddingInput] = Field(default_factory=list)


class EmbeddingResult(BaseModel):
    """Output of an embedding run."""

    vectors: list[EmbeddingVector] = Field(default_factory=list)
