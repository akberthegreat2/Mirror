"""Chunking capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import ChunkRequest, ChunkResult


@runtime_checkable
class Chunker(Protocol):
    """Protocol implemented by chunking providers."""

    async def chunk(self, request: ChunkRequest) -> ChunkResult:
        """Split documents into repeatable chunks."""
