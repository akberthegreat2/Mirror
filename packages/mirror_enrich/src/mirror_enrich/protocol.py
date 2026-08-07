"""Enrichment capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mirror_enrich.models import EnrichmentRequest, EnrichmentResult


@runtime_checkable
class Enricher(Protocol):
    """Protocol implemented by enrichment providers."""

    async def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        """Derive deterministic metadata for a batch of documents."""
