import pytest
from mirror_analyze.models import AnalyzeRequest, AnalyzeResult
from mirror_analyze_basic import Analyzer, BasicAnalyzeProvider


def test_analyzer_extracts_keywords() -> None:
    result = Analyzer().analyze("Hello world from Mirror")
    assert result.keywords
    assert result.token_count > 0


@pytest.mark.asyncio
async def test_basic_analyze_provider_works() -> None:
    result = await BasicAnalyzeProvider().analyze(AnalyzeRequest(text="Hello world"))
    assert isinstance(result, AnalyzeResult)
    assert result.analysis.keywords
