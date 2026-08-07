"""Compliance capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mirror_compliance.models import ComplianceRequest, ComplianceResult


@runtime_checkable
class ComplianceChecker(Protocol):
    """Protocol implemented by compliance providers."""

    async def check(self, request: ComplianceRequest) -> ComplianceResult:
        """Evaluate documents against policy rules."""
