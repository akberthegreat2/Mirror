"""Analyze capability protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import AnalyzeRequest, AnalyzeResult


@runtime_checkable
class Analyze(Protocol):
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResult: ...
