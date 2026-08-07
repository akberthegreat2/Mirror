"""Typed models for the Vector store capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class VectorStoreMode(str, Enum):
    """Supported vector store operations."""

    UPSERT = "upsert"
    QUERY = "query"


@dataclass(slots=True, frozen=True)
class VectorRecord:
    """A single stored vector with provenance metadata."""

    record_id: str
    vector: tuple[float, ...]
    document_id: str
    chunk_id: str | None = None
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class VectorMatch:
    """A ranked vector record match."""

    record: VectorRecord
    score: float


class VectorUpsertRequest(BaseModel):
    """Input for an upsert operation."""

    namespace: str = Field(default="default", min_length=1)
    records: list[VectorRecord] = Field(default_factory=list)


class VectorUpsertResult(BaseModel):
    """Output of an upsert operation."""

    namespace: str
    upserted: int


class VectorQueryRequest(BaseModel):
    """Input for a query operation."""

    namespace: str = Field(default="default", min_length=1)
    vector: list[float] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=100)
    filters: dict[str, Any] = Field(default_factory=dict)


class VectorQueryResult(BaseModel):
    """Output of a query operation."""

    namespace: str
    matches: list[VectorMatch] = Field(default_factory=list)


class VectorStoreRequest(BaseModel):
    """Polymorphic input for vector store operations."""

    mode: Literal["upsert", "query"]
    namespace: str = Field(default="default", min_length=1)
    records: list[VectorRecord] = Field(default_factory=list)
    vector: list[float] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=100)
    filters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mode(self) -> VectorStoreRequest:
        """Ensure the correct payload is supplied for each mode."""

        if self.mode == VectorStoreMode.UPSERT.value and not self.records:
            raise ValueError("records are required for upsert requests")
        if self.mode == VectorStoreMode.QUERY.value and not self.vector:
            raise ValueError("vector is required for query requests")
        return self


class VectorStoreResult(BaseModel):
    """Polymorphic output for vector store operations."""

    mode: Literal["upsert", "query"]
    namespace: str
    upserted: int = 0
    matches: list[VectorMatch] = Field(default_factory=list)
