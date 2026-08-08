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
- [x] Django control-plane package
- [x] Django admin metadata models
- [x] Django migrations and admin registrations
- [x] REST control-plane package
- [x] Pipeline blob repository and immutable versions
- [ ] Application-specific auth/role policy beyond Django model permissions
- [x] Admin views for runs, workers, crawled URLs, and archives

## Phase 4 — Beta runtime

- [x] Crawl persistence contracts
- [x] Scheduler backend
- [x] SQLite worker backend
- [x] PostgreSQL durable worker/metadata stores
- [ ] MySQL metadata store
- [x] Core blob storage boundary
- [x] Redis broker through Celery execution backend
- [x] Generic distributed workers and execution-class routing
- [x] Import/discovery/manifest certification tests
- [ ] Full live lab certification (requires live PostgreSQL/Redis/Celery environment)
- [ ] Compatibility matrix suite
- [x] Beta release checklist and certification documentation

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
- distributed execution and Celery worker integration (implemented; certification remains a deployment test);
- open-source-first provider policy;
- executor internal decomposition.

## Phase D — Certification and interface convergence

- [x] Interface-neutral manifest projection
- [x] CLI manifest inspection
- [x] Dashboard and REST interface manifests
- [x] Immutable managed pipeline versions
- [x] Repository-wide ruff gate
- [x] Repository-wide mypy gate
- [x] Django migration smoke
- [x] Capability/provider manifest certification
- [x] Final documentation and handover review
