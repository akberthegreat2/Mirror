"""Deterministic hash-based embedding provider."""

from __future__ import annotations

import hashlib
import math
import re

from mirror_core.extensions.models import ProviderManifest
from mirror_embedding.models import (
    EmbeddingInput,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingVector,
)
from mirror_embedding.protocol import Embedder
from mirror_embedding.settings import EmbeddingSettings

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")


class HashEmbeddingProvider(Embedder):
    """Embed text into a stable, unit-length hash space."""

    def __init__(self, settings: EmbeddingSettings | None = None) -> None:
        self._settings = settings or EmbeddingSettings()

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Embed a batch of inputs."""

        vectors = [self._embed_item(item) for item in request.items]
        return EmbeddingResult(vectors=vectors)

    def _embed_item(self, item: EmbeddingInput) -> EmbeddingVector:
        vector = [0.0] * self._settings.dimension
        for token in self._tokenize(item.text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % self._settings.dimension
            vector[index] += 1.0

        if self._settings.normalize:
            norm = math.sqrt(sum(value * value for value in vector))
            if norm:
                vector = [value / norm for value in vector]

        return EmbeddingVector(
            item_id=item.item_id,
            values=tuple(vector),
            metadata=dict(item.metadata),
        )

    def _tokenize(self, text: str) -> list[str]:
        return [token.casefold() for token in _TOKEN_PATTERN.findall(text)]


provider = ProviderManifest(
    name="hash",
    capability="embedding",
    capability_api="~=1.0",
    factory="mirror_embedding_hash.provider:HashEmbeddingProvider",
    settings_model="mirror_embedding.settings:EmbeddingSettings",
    metadata={"description": "Deterministic hash embedding provider."},
)
