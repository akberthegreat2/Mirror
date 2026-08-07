"""Mirror Embedding capability – turn text into stable vectors."""

from mirror_embedding.capability import capability
from mirror_embedding.errors import EmbeddingError
from mirror_embedding.models import (
    EmbeddingInput,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingVector,
)
from mirror_embedding.protocol import Embedder
from mirror_embedding.runner import embed_step
from mirror_embedding.settings import EmbeddingSettings

__all__ = [
    "Embedder",
    "EmbeddingError",
    "EmbeddingInput",
    "EmbeddingRequest",
    "EmbeddingResult",
    "EmbeddingSettings",
    "EmbeddingVector",
    "capability",
    "embed_step",
]
