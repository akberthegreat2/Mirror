"""Tests for the analyze capability package."""

from __future__ import annotations

import pytest
from mirror_analyze import AnalyzeRequest, AnalyzeResult, analyze_step, capability
from mirror_analyze_basic import Analyzer, BasicAnalyzeProvider


class FakeAnalyzeProvider:
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResult:
        return AnalyzeResult(analysis=Analyzer().analyze(request.text))


def test_capability_descriptor() -> None:
    assert capability.name == "analyze"
    assert capability.request_model == AnalyzeRequest
    assert capability.result_model == AnalyzeResult
    assert capability.runner == "mirror_analyze.runner:analyze_step"


def test_analyzer_extracts_keywords() -> None:
    result = Analyzer().analyze("Hello world from Mirror")
    assert result.keywords
    assert result.token_count > 0


@pytest.mark.asyncio
async def test_analyze_step() -> None:
    result = await analyze_step(
        FakeAnalyzeProvider(), AnalyzeRequest(text="Hello world from Mirror")
    )
    assert result.analysis.keywords


@pytest.mark.asyncio
async def test_basic_analyze_provider() -> None:
    result = await BasicAnalyzeProvider().analyze(
        AnalyzeRequest(text="Hello world from Mirror")
    )
    assert result.analysis.keywords
