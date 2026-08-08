"""Tests for the diff capability package."""

from __future__ import annotations

import pytest
from mirror_diff import DiffRequest, DiffResult, capability, diff_step
from mirror_diff_text import DiffEngine, TextDiffProvider


class FakeDiffProvider:
    async def diff(self, request: DiffRequest) -> DiffResult:
        return DiffResult(summary=DiffEngine().compare(request.before, request.after))


def test_capability_descriptor() -> None:
    assert capability.name == "diff"
    assert capability.request_model == DiffRequest
    assert capability.result_model == DiffResult
    assert capability.runner == "mirror_diff.runner:diff_step"


def test_diff_engine_detects_change() -> None:
    summary = DiffEngine().compare("hello", "hello world")
    assert summary.changed is True
    assert summary.ratio < 1.0


@pytest.mark.asyncio
async def test_diff_step() -> None:
    result = await diff_step(FakeDiffProvider(), DiffRequest(before="hello", after="hello world"))
    assert result.summary.changed is True


@pytest.mark.asyncio
async def test_text_diff_provider() -> None:
    result = await TextDiffProvider().diff(DiffRequest(before="hello", after="hello world"))
    assert result.summary.changed is True
