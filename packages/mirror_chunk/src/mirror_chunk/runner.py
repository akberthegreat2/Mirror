"""Chunking runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_core.executor_support import RunnerContext

from .errors import ChunkError
from .models import ChunkRequest, ChunkResult
from .protocol import Chunker


async def chunk_step(
    provider: Chunker,
    request: ChunkRequest,
    runner_context: RunnerContext | None = None,
) -> ChunkResult:
    """Adapt a Chunker provider to the capability runner contract."""

    try:
        return await provider.chunk(request)
    except ChunkError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise ChunkError(
            f"Failed to chunk {len(request.documents)} document(s)",
            details={"documents": len(request.documents)},
            cause=exc,
        ) from exc
