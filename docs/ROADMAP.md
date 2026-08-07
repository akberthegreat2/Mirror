# Mirror Roadmap

## Phase 1 — Frozen alpha core

- [x] Capability-agnostic core
- [x] Discovery and registry
- [x] Middleware contract
- [x] Worker contracts
- [x] Signals
- [x] Fresh-install smoke test
- [x] `mirror startproject`
- [x] `mirror doctor`
- [x] Alpha contract and release checklist

## Phase 2 — Modularity proof

- [x] One capability with two providers
- [x] Provider swap integration test
- [x] `mirror_fetch_playwright` package
- [x] Provider documentation
- [x] Extension-system migration audit from legacy registry language to the canonical extension API

## Phase 3 — Django control plane

- [x] `mirror startapp`
- [x] Project template polish
- [x] Better CLI help and diagnostics
- [x] Workspace bootstrap docs (`conftest.py`, `sitecustomize.py`)
- [x] End-to-end developer guide
- [ ] Django control-plane package
- [ ] Django admin metadata models
- [ ] Auth and roles for operators
- [ ] Admin views for runs, workers, crawled URLs, and archives

## Phase 4 — Beta runtime

- [ ] Crawl persistence
- [ ] Scheduler backend
- [ ] SQLite worker backend
- [ ] PostgreSQL / MySQL metadata store
- [ ] Blob storage adapters
- [ ] Redis-backed queue / cache integration
- [ ] Import smoke tests for every package
- [ ] Discovery smoke tests for every package
- [ ] Contract smoke tests for every package
- [ ] Lab certification suite
- [ ] Compatibility matrix suite
- [ ] Beta release checklist

## Phase 5 — Knowledge infrastructure (initial slice)

- [x] Normalization capability family
- [x] Enrichment capability family
- [x] Chunking capability family
- [x] Deduplication capability family
- [x] Embedding providers
- [x] Vector store providers
- [x] Retrieval capability family
- [x] Provenance contracts
- [x] Compliance and policy contracts
- [x] LLMs stay outside Mirror Core; only optional providers and consumers are allowed

## Phase 6 — Ecosystem catalog and optional plugin growth

- [ ] OCR and document parsing providers
- [ ] Stealth and proxy providers
- [ ] RPA and agentic crawl providers
- [ ] Geospatial and maps providers
- [ ] Monitoring and webhook providers
- [ ] AI/ML training and serving providers
- [ ] Domain-specific long-tail capability catalogs
- [x] Open-source-first default provider guidance

## Proposed architecture directions

The following ideas are tracked as proposed ADRs rather than alpha commitments:

- trusted execution pipeline;
- extension model and plugin lifecycle;
- distributed execution and Celery worker integration;
- open-source-first provider policy;
- executor internal decomposition.
