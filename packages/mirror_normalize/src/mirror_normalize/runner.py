"""Normalization runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import NormalizationError
from .models import NormalizationRequest, NormalizationResult
from .protocol import Normalizer


async def normalize_step(
    provider: Normalizer, request: NormalizationRequest
) -> NormalizationResult:
    """Adapt a Normalizer provider to the capability runner contract."""

    try:
        return await provider.normalize(request)
    except NormalizationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise NormalizationError(
            f"Failed to normalize {len(request.documents)} document(s)",
            details={"documents": len(request.documents)},
            cause=exc,
        ) from exc
