"""Deduplication capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mirror_dedup.models import DedupRequest, DedupResult


@runtime_checkable
class Deduplicator(Protocol):
    """Protocol implemented by deduplication providers."""

    async def dedup(self, request: DedupRequest) -> DedupResult:
        """Collapse duplicate documents into canonical records."""
