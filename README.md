# Mirror

Mirror is a Python framework for building capability-driven products.

It helps you:
- crawl and fetch content;
- archive pages, responses, and blobs;
- monitor changes over time;
- normalize, chunk, embed, store, and retrieve knowledge;
- run recurring work with workers and a scheduler;
- build control-plane tooling and product interfaces around the same kernel.

Mirror is open-source-first and vendor-neutral.
Core never depends on proprietary AI vendors or SaaS services.
If a provider exists for a closed service, it is optional and external.
Preferred defaults in the documentation use self-hostable and open-source providers such as Ollama, sentence-transformers, Qdrant, pgvector, Camoufox, Tesseract, PyMuPDF, and similar packages.

## What Mirror can do today

Mirror already ships a real kernel and a working ecosystem:

- a capability-agnostic core runtime;
- installable capabilities such as fetch, archive, crawl, search, analyze, scrape, diff, monitor, normalize, enrich, chunk, dedup, embedding, provenance, compliance, retrieval, and vector storage;
- replaceable providers for those capabilities;
- middleware, signals, metadata storage, scheduling, workers, and lifecycle management in Core;
- a trusted execution pipeline that compiles a DAG into an execution plan;
- a manifest-driven extension model in Core;
- a knowledge-infrastructure slice that can normalize text, chunk documents, embed content, store vectors, and retrieve matches;
- install, import, and contract smoke tests that prove the packages fit together.

## How Mirror works

Mirror follows a simple algorithm:

1. You describe work as a capability pipeline or use one of the shipped commands and scaffold templates.
2. Mirror discovers the available capability, provider, middleware, worker, and storage packages.
3. The planner validates the graph, selects providers, and compiles an execution plan.
4. The executor runs only the compiled plan.
5. Middleware observes, annotates, short-circuits, retries, or measures the run.
6. Workers, storage, and metadata backends record progress and results.
7. Signals report what happened without controlling the run.

That is the whole shape of the kernel.

## Ways to use Mirror

### 1) Use the CLI

The CLI is the fastest way to try Mirror:

```bash
pip install -e .[dev]
mirror startproject demo
cd demo
mirror doctor
mirror startapp monitor
mirror worker --backend sqlite
```

The CLI is useful when you want the scaffold, diagnostics, or a runnable local project without building everything yourself.

### 2) Use the scaffold project

`mirror startproject` creates a real project layout, including:

- `manage.py`
- app folders
- settings
- tests
- docs

This is the path for a new Mirror-powered app or service.

### 3) Use Mirror inside a custom project

If you already have a Python project, Mirror can be added as a kernel plus a set of packages:

- Core for execution and orchestration;
- capabilities for domain contracts;
- providers for concrete behavior;
- optional interface packages for CLI, API, admin, or dashboards.

This is the path for teams that already have an application and want Mirror as the workflow engine behind it.

### 4) Use Mirror in a single script or prototype

For experiments, you can wire a minimal stack in one file:

- load the core;
- choose one capability;
- select one provider;
- run a plan;
- inspect the returned resources.

That path is useful for proofs of concept, tests, and demos.

## Current package families

Mirror currently includes families for:

- fetch and archive;
- crawl and monitoring;
- search, analyze, scrape, and diff;
- normalization, enrichment, chunking, deduplication, embeddings, provenance, retrieval, compliance, and vector storage;
- workers, metadata, scheduler, and storage;
- CLI and testing helpers.

The exact package list lives in the reference docs.

## Future direction

Mirror is growing into a broader capability kernel, but the roadmap is still controlled.

Near-term work focuses on:

- extension-system migration audit;
- Docker Compose development stack;
- Redis and Celery worker backends;
- PostgreSQL metadata store;
- install smoke tests;
- import smoke tests;
- discovery smoke tests;
- contract smoke tests;
- lab certification tests;
- control-plane cleanup;
- better developer experience.

The longer-term ecosystem includes open-source-first plugins for OCR, PDF, stealth, proxy management, RPA, document parsing, vector search, and knowledge workflows.

Far-future ideas are tracked in the ecosystem catalog and future docs rather than being promised as core features.

## Docs map

- `docs/ARCHITECTURE.md` — the constitutional architecture contract.
- `docs/ROADMAP.md` — current phases and delivery gates.
- `docs/FUTURE.md` — deferred work and long-term direction.
- `docs/ecosystem/` — current and future capability catalog.
- `docs/testing/` — smoke tests, lab certification, and reference test sites.
- `docs/adr/` — architecture decision records.
- `docs/PRs/` — implementation phase notes.
- `docs/reference/` — package and command references.
- `docs/tutorials/` — step-by-step guides.
- `docs/concepts/` — framework concepts.
- `CONTRIBUTING.md` — contributor workflow and quality requirements.

## Verification

Run the test suite from the repository root:

```bash
pytest
```

Mirror also ships install and import smoke tests so every package can prove that it installs, imports, and registers cleanly before it reaches beta.
