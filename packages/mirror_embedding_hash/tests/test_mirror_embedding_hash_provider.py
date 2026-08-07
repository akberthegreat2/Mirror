"""Tests for the hash embedding provider."""

from __future__ import annotations

import pytest
from mirror_embedding.models import EmbeddingInput, EmbeddingRequest
from mirror_embedding_hash.provider import HashEmbeddingProvider, provider


@pytest.mark.asyncio
async def test_hash_embedding_provider_is_deterministic() -> None:
    """Provider should generate stable, unit-length vectors."""

    provider_impl = HashEmbeddingProvider()
    request = EmbeddingRequest(
        items=[EmbeddingInput(item_id="item-1", text="hello world")]
    )

    result_one = await provider_impl.embed(request)
    result_two = await provider_impl.embed(request)

    assert result_one == result_two
    vector = result_one.vectors[0].values
    assert len(vector) == 64
    assert pytest.approx(sum(value * value for value in vector), rel=1e-6) == 1.0


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "hash"
    assert provider.capability == "embedding"
    assert provider.factory == "mirror_embedding_hash.provider:HashEmbeddingProvider"
