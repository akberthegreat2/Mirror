"""Analyze runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import AnalyzeError
from .models import AnalyzeRequest, AnalyzeResult
from .protocol import Analyze


async def analyze_step(provider: Analyze, request: AnalyzeRequest) -> AnalyzeResult:
    try:
        return await provider.analyze(request)
    except AnalyzeError:
        raise
    except Exception as exc:
        raise AnalyzeError("Failed to analyze content", cause=exc) from exc
