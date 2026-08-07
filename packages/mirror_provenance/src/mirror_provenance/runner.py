"""Provenance runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_provenance.errors import ProvenanceError
from mirror_provenance.models import ProvenanceRequest, ProvenanceResult
from mirror_provenance.protocol import Provenancer


async def provenance_step(
    provider: Provenancer, request: ProvenanceRequest
) -> ProvenanceResult:
    """Adapt a Provenancer provider to the capability runner contract."""

    try:
        return await provider.provenance(request)
    except ProvenanceError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise ProvenanceError(
            f"Failed to create provenance for {len(request.envelopes)} payload(s)",
            details={"envelopes": len(request.envelopes)},
            cause=exc,
        ) from exc
