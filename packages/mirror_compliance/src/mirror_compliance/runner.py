"""Compliance runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from mirror_compliance.errors import ComplianceError
from mirror_compliance.models import ComplianceRequest, ComplianceResult
from mirror_compliance.protocol import ComplianceChecker


async def compliance_step(
    provider: ComplianceChecker, request: ComplianceRequest
) -> ComplianceResult:
    """Adapt a ComplianceChecker provider to the capability runner contract."""

    try:
        return await provider.check(request)
    except ComplianceError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise ComplianceError(
            f"Failed to evaluate compliance for {len(request.documents)} document(s)",
            details={"documents": len(request.documents)},
            cause=exc,
        ) from exc
