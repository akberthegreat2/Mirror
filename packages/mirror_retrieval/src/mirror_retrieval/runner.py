"""Retrieval runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_core.executor_support import RunnerContext

from .errors import RetrievalError
from .models import RetrievalRequest, RetrievalResult
from .protocol import Retriever


async def retrieval_step(
    provider: Retriever,
    request: RetrievalRequest,
    runner_context: RunnerContext | None = None,
) -> RetrievalResult:
    """Adapt a Retriever provider to the capability runner contract."""

    try:
        return await provider.retrieve(request)
    except RetrievalError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise RetrievalError(
            f"Failed to retrieve matches for '{request.query}'",
            details={"query": request.query},
            cause=exc,
        ) from exc
