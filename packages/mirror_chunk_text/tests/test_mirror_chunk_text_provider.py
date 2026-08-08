"""Tests for the chunking provider."""

from __future__ import annotations

import pytest
from mirror_chunk.models import ChunkDocument, ChunkRequest
from mirror_chunk.settings import ChunkSettings
from mirror_chunk_text.provider import TextChunkProvider, provider


@pytest.mark.asyncio
async def test_text_chunk_provider_chunks_with_overlap() -> None:
    """Provider should produce stable overlap-aware chunks."""

    provider_impl = TextChunkProvider(ChunkSettings(chunk_size=3, chunk_overlap=1))
    request = ChunkRequest(
        documents=[ChunkDocument(document_id="doc-1", text="one two three four five")]
    )

    result = await provider_impl.chunk(request)

    assert [chunk.text for chunk in result.chunks] == [
        "one two three",
        "three four five",
    ]
    assert result.chunks[0].metadata["chunk_index"] == 0
    assert result.chunks[1].start_token == 2


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "text"
    assert provider.capability == "chunk"
    assert provider.factory == "mirror_chunk_text.provider:TextChunkProvider"
