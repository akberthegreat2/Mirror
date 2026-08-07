"""Enrichment runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_enrich.errors import EnrichmentError
from mirror_enrich.models import EnrichmentRequest, EnrichmentResult
from mirror_enrich.protocol import Enricher


async def enrich_step(
    provider: Enricher, request: EnrichmentRequest
) -> EnrichmentResult:
    """Adapt an Enricher provider to the capability runner contract."""

    try:
        return await provider.enrich(request)
    except EnrichmentError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise EnrichmentError(
            f"Failed to enrich {len(request.documents)} document(s)",
            details={"documents": len(request.documents)},
            cause=exc,
        ) from exc
