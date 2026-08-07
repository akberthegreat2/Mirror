"""Vector store capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    VectorQueryRequest,
    VectorQueryResult,
    VectorUpsertRequest,
    VectorUpsertResult,
)


@runtime_checkable
class VectorStore(Protocol):
    """Protocol implemented by vector store providers."""

    async def upsert(self, request: VectorUpsertRequest) -> VectorUpsertResult:
        """Store or replace vector records in a namespace."""

    async def query(self, request: VectorQueryRequest) -> VectorQueryResult:
        """Return the nearest records for a query vector."""
