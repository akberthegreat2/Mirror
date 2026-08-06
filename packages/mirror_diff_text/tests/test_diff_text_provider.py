import pytest
from mirror_diff.models import DiffRequest, DiffResult
from mirror_diff_text import DiffEngine, TextDiffProvider


def test_diff_engine_detects_change() -> None:
    summary = DiffEngine().compare("hello", "hello world")
    assert summary.changed is True
    assert summary.ratio < 1.0


@pytest.mark.asyncio
async def test_text_diff_provider_works() -> None:
    result = await TextDiffProvider().diff(
        DiffRequest(before="hello", after="hello world")
    )
    assert isinstance(result, DiffResult)
    assert result.summary.changed is True
