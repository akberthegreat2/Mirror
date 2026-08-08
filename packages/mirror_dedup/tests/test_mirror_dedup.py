"""Tests for the Deduplication capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_dedup.capability import capability
from mirror_dedup.errors import DedupError
from mirror_dedup.models import (
    DedupDocument,
    DeduplicatedDocument,
    DedupRequest,
    DedupResult,
)
from mirror_dedup.runner import dedup_step
from mirror_dedup.settings import DedupSettings


@pytest.mark.asyncio
async def test_dedup_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = DedupRequest(documents=[DedupDocument(document_id="doc-1", text="Mirror")])
    expected = DedupResult(
        documents=[
            DeduplicatedDocument(
                document_id="doc-1",
                text="Mirror",
                fingerprint="abc",
                duplicate_count=0,
            )
        ],
        duplicates=[],
        removed_count=0,
    )
    provider.dedup.return_value = expected

    result = await dedup_step(provider, request)

    provider.dedup.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_dedup_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in DedupError."""

    provider = AsyncMock()
    provider.dedup.side_effect = ValueError("boom")
    request = DedupRequest(documents=[DedupDocument(document_id="doc-1", text="Mirror")])

    with pytest.raises(DedupError) as excinfo:
        await dedup_step(provider, request)

    assert "Failed to deduplicate" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "dedup"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == DedupRequest
    assert capability.result_model == DedupResult
    assert capability.settings_model == DedupSettings
