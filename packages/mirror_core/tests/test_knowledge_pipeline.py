"""End-to-end tests for the knowledge-infrastructure slice."""

from __future__ import annotations

from uuid import uuid4

import pytest
from mirror_chunk.models import ChunkDocument, ChunkRequest
from mirror_chunk_text.provider import TextChunkProvider
from mirror_compliance.models import (
    ComplianceDocument,
    ComplianceRequest,
    ComplianceRule,
)
from mirror_compliance_rules.provider import RulesComplianceProvider
from mirror_core.resource import ProducerRef
from mirror_dedup.models import DedupDocument, DedupRequest
from mirror_dedup_hash.provider import HashDedupProvider
from mirror_embedding.models import EmbeddingInput, EmbeddingRequest
from mirror_embedding_hash.provider import HashEmbeddingProvider
from mirror_enrich.models import EnrichmentDocument, EnrichmentRequest
from mirror_enrich_text.provider import TextEnrichmentProvider
from mirror_normalize.models import NormalizationDocument, NormalizationRequest
from mirror_normalize_text.provider import TextNormalizationProvider
from mirror_provenance.models import ProvenanceInput, ProvenanceRequest
from mirror_provenance_resource.provider import ResourceProvenanceProvider
from mirror_retrieval.models import RetrievalRequest
from mirror_retrieval_memory.provider import MemoryRetrievalProvider
from mirror_vectorstore.models import VectorRecord, VectorUpsertRequest
from mirror_vectorstore_memory.provider import MemoryVectorStoreProvider
from pydantic import BaseModel


class ChunkPayload(BaseModel):
    """A simple provenance payload used in the knowledge pipeline."""

    chunk_id: str
    document_id: str
    text: str
    summary: str


@pytest.mark.asyncio
async def test_knowledge_slice_runs_through_normalize_enrich_dedup_chunk_embed_store_retrieve() -> (
    None
):
    """A knowledge request should flow through the full deterministic pipeline."""

    normalizer = TextNormalizationProvider()
    enricher = TextEnrichmentProvider()
    deduplicator = HashDedupProvider()
    chunker = TextChunkProvider()
    embedder = HashEmbeddingProvider()
    vector_store = MemoryVectorStoreProvider()
    retriever = MemoryRetrievalProvider(
        embedder=embedder,
        vector_store=vector_store,
    )
    provenance = ResourceProvenanceProvider()
    compliance = RulesComplianceProvider()

    raw_documents = NormalizationRequest(
        documents=[
            NormalizationDocument(
                document_id="doc-1",
                text="The cat sat on the mat.",
                metadata={"source": "story"},
            ),
            NormalizationDocument(
                document_id="doc-2",
                text="Mirror normalizes text, enriches it, deduplicates it, and retrieves the best chunk.",
                metadata={"source": "knowledge"},
            ),
            NormalizationDocument(
                document_id="doc-3",
                text="Mirror normalizes text, enriches it, deduplicates it, and retrieves the best chunk.",
                metadata={"source": "knowledge"},
            ),
        ]
    )
    normalized = await normalizer.normalize(raw_documents)

    enriched = await enricher.enrich(
        EnrichmentRequest(
            documents=[
                EnrichmentDocument(
                    document_id=document.document_id,
                    text=document.normalized_text,
                    metadata=document.metadata,
                )
                for document in normalized.documents
            ]
        )
    )
    assert "deduplicates" in enriched.documents[1].keywords

    deduped = await deduplicator.dedup(
        DedupRequest(
            documents=[
                DedupDocument(
                    document_id=document.document_id,
                    text=document.enriched_text,
                    metadata=document.metadata,
                )
                for document in enriched.documents
            ]
        )
    )
    assert len(deduped.documents) == 2
    assert deduped.removed_count == 1

    compliance_result = await compliance.check(
        ComplianceRequest(
            documents=[
                ComplianceDocument(
                    document_id=document.document_id,
                    text=document.text,
                    metadata=document.metadata,
                )
                for document in deduped.documents
            ],
            rules=[
                ComplianceRule(
                    rule_id="must-have-source",
                    required_metadata_keys=("source",),
                    min_unique_words=3,
                )
            ],
        )
    )
    assert compliance_result.compliant is True

    chunk_documents = ChunkRequest(
        documents=[
            ChunkDocument(
                document_id=document.document_id,
                text=document.text,
                metadata=document.metadata,
            )
            for document in deduped.documents
        ]
    )
    chunked = await chunker.chunk(chunk_documents)
    assert chunked.chunks

    provenance_result = await provenance.provenance(
        ProvenanceRequest(
            envelopes=[
                ProvenanceInput(
                    resource_type="ChunkPayload",
                    schema_version="1.0",
                    payload=ChunkPayload(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        summary=chunk.text[:24],
                    ),
                    producer=ProducerRef(
                        capability="chunk",
                        capability_version="1.0.0",
                        provider="text",
                    ),
                    parents=[uuid4()],
                    metadata=dict(chunk.metadata),
                )
                for chunk in chunked.chunks
            ]
        )
    )
    assert len(provenance_result.envelopes) == len(chunked.chunks)
    assert all(envelope.fingerprint for envelope in provenance_result.envelopes)
    assert {
        envelope.metadata["source"] for envelope in provenance_result.envelopes
    } == {"knowledge", "story"}
    assert all(len(envelope.parents) == 1 for envelope in provenance_result.envelopes)

    embeddings = await embedder.embed(
        EmbeddingRequest(
            items=[
                EmbeddingInput(
                    item_id=chunk.chunk_id, text=chunk.text, metadata=chunk.metadata
                )
                for chunk in chunked.chunks
            ]
        )
    )
    records = [
        VectorRecord(
            record_id=vector.item_id,
            vector=vector.values,
            document_id=chunked.chunks[index].document_id,
            chunk_id=chunked.chunks[index].chunk_id,
            text=chunked.chunks[index].text,
            metadata=chunked.chunks[index].metadata,
        )
        for index, vector in enumerate(embeddings.vectors)
    ]
    await vector_store.upsert(VectorUpsertRequest(records=records))

    result = await retriever.retrieve(
        RetrievalRequest(query="How does Mirror retrieve the best chunk?", top_k=1)
    )

    assert result.matches
    assert result.matches[0].document_id == "doc-2"
    assert "knowledge" in result.matches[0].metadata["source"]
