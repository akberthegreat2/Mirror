"""Tests for the retrieval provider."""

from __future__ import annotations

import pytest
from mirror_embedding.models import (
    EmbeddingInput,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingVector,
)
from mirror_embedding_hash.provider import HashEmbeddingProvider
from mirror_retrieval.models import RetrievalRequest
from mirror_retrieval_memory.provider import (
    MemoryRetrievalProvider,
    build_provider,
    provider,
)
from mirror_vectorstore.models import (
    VectorMatch,
    VectorQueryRequest,
    VectorQueryResult,
    VectorRecord,
    VectorUpsertRequest,
)
from mirror_vectorstore_memory.provider import MemoryVectorStoreProvider


@pytest.mark.asyncio
async def test_memory_retrieval_provider_accepts_injected_dependencies() -> None:
    """Provider instances should accept explicit embedder and store contracts."""

    class FakeEmbedder:
        async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
            return EmbeddingResult(
                vectors=[
                    EmbeddingVector(
                        item_id=request.items[0].item_id,
                        values=(1.0, 0.0, 0.0),
                        metadata={"source": "fake-embedder"},
                    )
                ]
            )

    class FakeVectorStore:
        async def query(self, request: VectorQueryRequest) -> VectorQueryResult:
            return VectorQueryResult(
                namespace=request.namespace,
                matches=[
                    VectorMatch(
                        record=VectorRecord(
                            record_id="record-1",
                            vector=tuple(request.vector),
                            document_id="doc-1",
                            chunk_id="chunk-1",
                            text="relevant text",
                            metadata={"source": "fake-store"},
                        ),
                        score=0.99,
                    )
                ],
            )

    retriever = MemoryRetrievalProvider(
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(),
    )

    result = await retriever.retrieve(RetrievalRequest(query="knowledge"))

    assert result.matches[0].document_id == "doc-1"
    assert result.matches[0].metadata == {"source": "fake-store"}


@pytest.mark.asyncio
async def test_memory_retrieval_provider_ranks_relevant_documents() -> None:
    """Provider should retrieve the document that shares query terms."""

    embedder = HashEmbeddingProvider()
    store = MemoryVectorStoreProvider()
    query_text = "vector retrieval pipeline"
    documents = [
        ("doc-1", "The cat sat on the mat."),
        ("doc-2", "A vector retrieval pipeline uses embeddings and a vector store."),
    ]
    records: list[VectorRecord] = []
    for doc_id, text in documents:
        embedding = await embedder.embed(
            EmbeddingRequest(items=[EmbeddingInput(item_id=doc_id, text=text)])
        )
        records.append(
            VectorRecord(
                record_id=f"{doc_id}:0",
                vector=embedding.vectors[0].values,
                document_id=doc_id,
                chunk_id=f"{doc_id}:0",
                text=text,
                metadata={"source": "test"},
            )
        )

    await store.upsert(VectorUpsertRequest(records=records))
    provider_impl = MemoryRetrievalProvider(embedder=embedder, vector_store=store)

    result = await provider_impl.retrieve(RetrievalRequest(query=query_text, top_k=1))

    assert result.matches[0].document_id == "doc-2"
    assert result.matches[0].metadata == {"source": "test"}


def test_build_provider_uses_configurable_factories(monkeypatch) -> None:
    """The provider factory should build dependencies from configured factories."""

    calls: list[tuple[str, dict[str, object]]] = []

    class StubDependency:
        def __init__(self, settings=None) -> None:
            self.settings = settings

    def fake_build(factory_path: str, settings):
        calls.append((factory_path, settings.model_dump()))
        return StubDependency(settings=settings)

    import importlib

    retrieval_provider = importlib.import_module("mirror_retrieval_memory.provider")
    monkeypatch.setattr(retrieval_provider, "_build_dependency", fake_build)
    from mirror_retrieval.settings import RetrievalSettings

    built = build_provider(
        RetrievalSettings(
            embedder_factory="mirror_embedding_hash.provider:HashEmbeddingProvider",
            embedder_settings={"dimension": 16},
            vector_store_factory="mirror_vectorstore_memory.provider:MemoryVectorStoreProvider",
            vector_store_settings={"default_namespace": "knowledge"},
        )
    )

    assert isinstance(built, MemoryRetrievalProvider)
    assert calls == [
        (
            "mirror_embedding_hash.provider:HashEmbeddingProvider",
            {"dimension": 16, "normalize": True},
        ),
        (
            "mirror_vectorstore_memory.provider:MemoryVectorStoreProvider",
            {"default_namespace": "knowledge"},
        ),
    ]


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "memory"
    assert provider.capability == "retrieval"
    assert provider.factory == "mirror_retrieval_memory.provider:build_provider"


def test_build_provider_uses_settings() -> None:
    """The provider factory should accept retrieval settings."""

    from mirror_retrieval.settings import RetrievalSettings

    built = build_provider(RetrievalSettings())
    assert isinstance(built, MemoryRetrievalProvider)


@pytest.mark.asyncio
async def test_memory_retrieval_provider_exposes_provenance() -> None:
    """The retrieval provider should preserve source provenance in hits."""
    embedder = HashEmbeddingProvider()
    store = MemoryVectorStoreProvider()
    text = "Mirror stores knowledge with provenance."
    embedding = await embedder.embed(
        EmbeddingRequest(items=[EmbeddingInput(item_id="doc-1", text=text)])
    )
    record = VectorRecord(
        record_id="doc-1:0",
        vector=embedding.vectors[0].values,
        document_id="doc-1",
        chunk_id="doc-1:0",
        text=text,
        metadata={"provenance": {"source_resource_id": "res-1", "chunk_index": 0}},
    )
    await store.upsert(VectorUpsertRequest(records=[record]))
    provider_impl = MemoryRetrievalProvider(embedder=embedder, vector_store=store)

    result = await provider_impl.retrieve(RetrievalRequest(query="provenance", top_k=1))

    assert result.matches[0].provenance["source_resource_id"] == "res-1"
    assert result.matches[0].score_details["similarity"] >= 0.0
    assert result.evaluation["top_k"] == 1
