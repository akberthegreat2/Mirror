"""Provenance capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mirror_provenance.models import ProvenanceRequest, ProvenanceResult


@runtime_checkable
class Provenancer(Protocol):
    """Protocol implemented by provenance providers."""

    async def provenance(self, request: ProvenanceRequest) -> ProvenanceResult:
        """Create immutable provenance envelopes for payloads."""
