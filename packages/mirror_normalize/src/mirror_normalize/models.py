"""Typed models for the Normalization capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class NormalizationDocument:
    """A raw document to normalize."""

    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class NormalizedDocument:
    """A normalized document snapshot."""

    document_id: str
    original_text: str
    normalized_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class NormalizationRequest(BaseModel):
    """Input for a normalization run."""

    documents: list[NormalizationDocument] = Field(default_factory=list)


class NormalizationResult(BaseModel):
    """Output of a normalization run."""

    documents: list[NormalizedDocument] = Field(default_factory=list)
