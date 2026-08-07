"""Embedding capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import EmbeddingRequest, EmbeddingResult


@runtime_checkable
class Embedder(Protocol):
    """Protocol implemented by embedding providers."""

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Embed a batch of inputs."""
