"""Tests for the Chunking capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_chunk.capability import capability
from mirror_chunk.errors import ChunkError
from mirror_chunk.models import Chunk, ChunkDocument, ChunkRequest, ChunkResult
from mirror_chunk.runner import chunk_step
from mirror_chunk.settings import ChunkSettings
from pydantic import ValidationError


def test_chunk_settings_validate_overlap() -> None:
    """Chunk settings should reject overlap that is not smaller than the chunk size."""

    with pytest.raises(ValidationError):
        ChunkSettings(chunk_size=16, chunk_overlap=16)


@pytest.mark.asyncio
async def test_chunk_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = ChunkRequest(
        documents=[ChunkDocument(document_id="doc-1", text="one two three four")]
    )
    expected = ChunkResult(
        chunks=[
            Chunk(
                chunk_id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                text="one two three four",
                start_token=0,
                end_token=4,
            )
        ]
    )
    provider.chunk.return_value = expected

    result = await chunk_step(provider, request)

    provider.chunk.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_chunk_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in ChunkError."""

    provider = AsyncMock()
    provider.chunk.side_effect = ValueError("boom")
    request = ChunkRequest(
        documents=[ChunkDocument(document_id="doc-1", text="one two three four")]
    )

    with pytest.raises(ChunkError) as excinfo:
        await chunk_step(provider, request)

    assert "Failed to chunk" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "chunk"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == ChunkRequest
    assert capability.result_model == ChunkResult
    assert capability.settings_model == ChunkSettings
