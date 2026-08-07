"""Deduplication runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_dedup.errors import DedupError
from mirror_dedup.models import DedupRequest, DedupResult
from mirror_dedup.protocol import Deduplicator


async def dedup_step(provider: Deduplicator, request: DedupRequest) -> DedupResult:
    """Adapt a Deduplicator provider to the capability runner contract."""

    try:
        return await provider.dedup(request)
    except DedupError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise DedupError(
            f"Failed to deduplicate {len(request.documents)} document(s)",
            details={"documents": len(request.documents)},
            cause=exc,
        ) from exc
