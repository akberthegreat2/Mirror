# ADR-0026 — Knowledge infrastructure capability model

## Status

Accepted

## Context

Mirror currently focuses on web-data acquisition, transformation, and durable
runtime behavior. The same capability/provider architecture can also support a
future knowledge-infrastructure direction without turning Mirror into an AI
framework or an LLM runtime.

The future goal is not to make Mirror depend on OpenAI, Anthropic, Gemini,
Ollama, Hugging Face, Qdrant, Pinecone, or any other vendor. The goal is to
prepare knowledge for downstream consumers while keeping `mirror_core`
vendor-agnostic.

## Decision

Mirror MAY grow a family of knowledge-oriented capabilities, each expressed as a
capability contract plus one or more provider packages.

The initial capability families are expected to include:

- normalization;
- enrichment;
- chunking;
- deduplication;
- embeddings;
- vector storage;
- retrieval;
- provenance;
- compliance.

These capabilities should follow the same architectural rules as Fetch and
Archive:

- capabilities define contracts, models, manifests, and tests;
- providers implement those contracts;
- the core kernel stays model-agnostic and vendor-agnostic;
- the LLM or agent layer stays outside `mirror_core`.

This means Mirror can support RAG-style and knowledge-management pipelines
without becoming a prompt framework, an agent framework, or a chat runtime.

## Consequences

- Mirror can evolve toward AI-native workflows without becoming AI-dependent;
- provider packages can cover OpenAI, Ollama, Sentence Transformers, Qdrant,
  pgvector, Weaviate, Milvus, and similar backends without changing the core;
- the same runtime can support classic web products and later knowledge
  products;
- a future contributor can add knowledge capabilities without creating a second
  framework.

## Implementation

The knowledge-infrastructure slice is shipped as the following packages:

- `mirror_normalize` and `mirror_normalize_text`;
- `mirror_enrich` and `mirror_enrich_text`;
- `mirror_chunk` and `mirror_chunk_text`;
- `mirror_dedup` and `mirror_dedup_hash`;
- `mirror_embedding` and `mirror_embedding_hash`;
- `mirror_vectorstore` and `mirror_vectorstore_memory`;
- `mirror_retrieval` and `mirror_retrieval_memory`;
- `mirror_provenance` and `mirror_provenance_resource`;
- `mirror_compliance` and `mirror_compliance_rules`.

These packages provide deterministic, first-party building blocks for text
normalization, enrichment, chunking, deduplication, embedding, provenance,
policy checks, vector storage, and retrieval without placing AI vendor SDKs
inside `mirror_core`. The first-party retrieval provider is configured through
dependency factory settings rather than hardcoded concrete imports, so its
embedding and vector-store backends remain swappable within the capability
contract.

## Robustness notes

The shipped knowledge slice is deterministic, but the next hardening step should make the retrieval surface more explicit about where every match came from. Recommended additions for future work:

- provenance-rich retrieval hits that expose source resource, chunk, and scoring details explicitly;
- a small golden-query evaluation harness so quality regressions are visible in CI;
- an optional hybrid-retrieval provider family (lexical + vector + rerank) for downstream LLM workflows.

These are not required for the current slice to function, but they are useful hardening additions for LLM-facing workloads.

## Non-goals

- embedding vendor SDKs into `mirror_core`;
- making LLM invocation part of the core runtime;
- building an inference engine;
- hardcoding one vector store or one embedding provider into a capability
  package;
- replacing the existing web-data framework direction with a rewrite.
