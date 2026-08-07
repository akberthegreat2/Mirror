"""Embedding runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import EmbeddingError
from .models import EmbeddingRequest, EmbeddingResult
from .protocol import Embedder


async def embed_step(provider: Embedder, request: EmbeddingRequest) -> EmbeddingResult:
    """Adapt an Embedder provider to the capability runner contract."""

    try:
        return await provider.embed(request)
    except EmbeddingError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise EmbeddingError(
            f"Failed to embed {len(request.items)} item(s)",
            details={"items": len(request.items)},
            cause=exc,
        ) from exc
