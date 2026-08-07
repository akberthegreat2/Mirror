# Future Work

This file collects ideas that are intentionally out of scope for the frozen alpha and the current beta gates.

## Beta blockers and near-term platform work

- extension-system migration audit and cleanup;
- Docker Compose development stack;
- Redis and Celery worker backends;
- PostgreSQL metadata store;
- import smoke tests;
- discovery smoke tests;
- contract smoke tests;
- lab certification tests;
- compatibility matrix tests;
- control-plane cleanup and operator workflow polish.

## Deferred to later releases

- distributed workers at cluster scale;
- dashboard and Django integration;
- REST and GraphQL interfaces;
- scheduling service beyond the documented backend contract;
- SaaS multi-tenancy;
- billing;
- Kubernetes orchestration;
- cluster scheduling.

## Open-source-first plugin policy

Mirror remains open-source-first and vendor-neutral.

Preferred defaults in docs and examples should use self-hostable or open-source providers such as:
- Ollama;
- sentence-transformers;
- Qdrant;
- pgvector;
- Camoufox;
- Playwright;
- SeleniumBase UC;
- Tesseract;
- PyMuPDF;
- pdfplumber;
- Camelot;
- Tabula;
- OpenTelemetry;
- Prometheus.

Optional proprietary adapters may exist as external plugins, but they do not define the framework.

## Near-future capability families

The following families are long-range extensions that may appear as separate capability packages and provider plugins:

- OCR and document parsing;
- stealth and proxy management;
- RPA and agentic crawling;
- LLM-based structured extraction;
- webhook gateways and operational integrations;
- geospatial and maps workflows;
- real-estate and public-record workflows;
- public social collection;
- email verification;
- observability exporters;
- privacy and compliance filters.

## Long-range ecosystem catalog

Mirror is also designed to host future capability families in:
- bioinformatics and life sciences;
- finance and quantitative trading;
- industrial IoT and manufacturing;
- multimedia and creative processing;
- database and ETL;
- desktop and OS automation;
- network and systems;
- AI/ML engineering beyond RAG;
- blockchain and Web3 off-chain data;
- geospatial and physical logistics;
- messaging and collaboration;
- legacy and mainframe;
- data privacy and security;
- scientific computing.

Those ideas are catalogued in `docs/ecosystem/FUTURE_CAPABILITIES.md`.

## Notes on ADR status

- ADR-0026 is implemented in this snapshot and no longer belongs to future work.
- ADR-0027 is implemented in the trusted execution pipeline.
- ADR-0028 is partially implemented through the manifest/discovery/lifecycle layer.
- ADR-0029 defines the runtime and worker semantics that the beta runtime builds on.
- ADR-0030, ADR-0031, and ADR-0032 cover metadata, scheduler, and distributed worker work.
- ADR-0033 defines the open-source-first provider policy.
