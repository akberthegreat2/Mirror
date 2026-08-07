"""Tests for the Retrieval capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_retrieval.capability import capability
from mirror_retrieval.errors import RetrievalError
from mirror_retrieval.models import RetrievalHit, RetrievalRequest, RetrievalResult
from mirror_retrieval.runner import retrieval_step
from mirror_retrieval.settings import RetrievalSettings


@pytest.mark.asyncio
async def test_retrieval_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = RetrievalRequest(query="vector search")
    expected = RetrievalResult(query="vector search", namespace="default", matches=[])
    provider.retrieve.return_value = expected

    result = await retrieval_step(provider, request)

    provider.retrieve.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_retrieval_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in RetrievalError."""

    provider = AsyncMock()
    provider.retrieve.side_effect = ValueError("boom")
    request = RetrievalRequest(query="vector search")

    with pytest.raises(RetrievalError) as excinfo:
        await retrieval_step(provider, request)

    assert "Failed to retrieve matches" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "retrieval"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == RetrievalRequest
    assert capability.result_model == RetrievalResult
    assert capability.settings_model == RetrievalSettings


@pytest.mark.asyncio
async def test_retrieval_hit_exposes_provenance() -> None:
    """Retrieval hits should surface provenance and scoring details."""
    provider = AsyncMock()
    provider.retrieve.return_value = RetrievalResult(
        query="vector search",
        namespace="default",
        matches=[
            RetrievalHit(
                record_id="record-1",
                document_id="doc-1",
                chunk_id="chunk-1",
                score=0.95,
                provenance={"source_resource_id": "res-1"},
                score_details={"similarity": 0.95},
            )
        ],
        evaluation={"top_k": 1},
    )

    result = await retrieval_step(provider, RetrievalRequest(query="vector search"))

    assert result.matches[0].provenance["source_resource_id"] == "res-1"
    assert result.matches[0].score_details["similarity"] == 0.95
    assert result.evaluation["top_k"] == 1
