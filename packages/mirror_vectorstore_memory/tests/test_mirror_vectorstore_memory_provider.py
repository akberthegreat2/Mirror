"""Tests for the memory vector store provider."""

from __future__ import annotations

import pytest
from mirror_vectorstore.models import (
    VectorQueryRequest,
    VectorRecord,
    VectorUpsertRequest,
)
from mirror_vectorstore_memory.provider import MemoryVectorStoreProvider, provider


@pytest.mark.asyncio
async def test_memory_vector_store_provider_queries_by_similarity() -> None:
    """Provider should rank records by cosine similarity."""

    store = MemoryVectorStoreProvider()
    await store.upsert(
        VectorUpsertRequest(
            records=[
                VectorRecord(
                    record_id="doc-1:0",
                    vector=(1.0, 0.0),
                    document_id="doc-1",
                    text="alpha",
                ),
                VectorRecord(
                    record_id="doc-2:0",
                    vector=(0.0, 1.0),
                    document_id="doc-2",
                    text="beta",
                ),
            ]
        )
    )

    result = await store.query(VectorQueryRequest(vector=[0.9, 0.1], top_k=1))

    assert result.matches[0].record.document_id == "doc-1"
    assert result.matches[0].score > 0.8


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "memory"
    assert provider.capability == "vectorstore"
    assert provider.factory == "mirror_vectorstore_memory.provider:MemoryVectorStoreProvider"
