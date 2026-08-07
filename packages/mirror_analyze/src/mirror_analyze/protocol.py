"""Analyze capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import AnalyzeRequest, AnalyzeResult


@runtime_checkable
class Analyze(Protocol):
    """Protocol for analysis providers."""

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResult: ...
