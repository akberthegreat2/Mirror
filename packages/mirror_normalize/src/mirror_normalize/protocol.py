"""Normalization capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import NormalizationRequest, NormalizationResult


@runtime_checkable
class Normalizer(Protocol):
    """Protocol implemented by normalization providers."""

    async def normalize(self, request: NormalizationRequest) -> NormalizationResult:
        """Normalize a batch of documents."""
