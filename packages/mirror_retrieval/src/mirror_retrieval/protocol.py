"""Retrieval capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import RetrievalRequest, RetrievalResult


@runtime_checkable
class Retriever(Protocol):
    """Protocol implemented by retrieval providers."""

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Return the most relevant vector-store matches for a query."""
