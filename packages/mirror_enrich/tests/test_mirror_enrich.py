"""Tests for the Enrichment capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_enrich.capability import capability
from mirror_enrich.errors import EnrichmentError
from mirror_enrich.models import (
    EnrichedDocument,
    EnrichmentDocument,
    EnrichmentRequest,
    EnrichmentResult,
    EnrichmentStatistics,
)
from mirror_enrich.runner import enrich_step
from mirror_enrich.settings import EnrichmentSettings


@pytest.mark.asyncio
async def test_enrich_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = EnrichmentRequest(documents=[EnrichmentDocument(document_id="doc-1", text="Hello Mirror.")])
    expected = EnrichmentResult(
        documents=[
            EnrichedDocument(
                document_id="doc-1",
                original_text="Hello Mirror.",
                enriched_text="Hello Mirror.",
                summary="Hello Mirror.",
                keywords=("hello", "mirror"),
                urls=(),
                statistics=EnrichmentStatistics(
                    character_count=13,
                    line_count=1,
                    sentence_count=1,
                    word_count=2,
                    unique_word_count=2,
                    keyword_count=2,
                    url_count=0,
                ),
            )
        ]
    )
    provider.enrich.return_value = expected

    result = await enrich_step(provider, request)

    provider.enrich.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_enrich_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in EnrichmentError."""

    provider = AsyncMock()
    provider.enrich.side_effect = ValueError("boom")
    request = EnrichmentRequest(documents=[EnrichmentDocument(document_id="doc-1", text="Hello Mirror.")])

    with pytest.raises(EnrichmentError) as excinfo:
        await enrich_step(provider, request)

    assert "Failed to enrich" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "enrich"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == EnrichmentRequest
    assert capability.result_model == EnrichmentResult
    assert capability.settings_model == EnrichmentSettings
