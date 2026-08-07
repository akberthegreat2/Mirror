# Capability packages

Mirror is split into separate capability packages. Each package owns one domain
contract and stays small on purpose.

## Package roles

| Package | Role |
| --- | --- |
| `mirror_core` | Framework kernel: planner, executor, registry, discovery, lifecycle, signals, middleware, storage, scheduler, workers |
| `mirror_fetch` | Fetch contract and request/result models |
| `mirror_fetch_httpx` | HTTPX provider for fetch |
| `mirror_fetch_playwright` | Playwright provider for fetch |
| `mirror_archive` | Archive contract and archive-specific orchestration |
| `mirror_archive_warc` | WARC archive provider |
| `mirror_crawl` | Crawl contract and crawl-specific orchestration |
| `mirror_crawl_local` | Local crawl provider composed from fetch |
| `mirror_search` | Search contract and search models |
| `mirror_search_memory` | First-party in-memory search provider |
| `mirror_analyze` | Analyze contract and analysis models |
| `mirror_analyze_basic` | First-party analyze provider |
| `mirror_scrape` | Scrape contract and extraction models |
| `mirror_scrape_basic` | First-party scrape provider |
| `mirror_diff` | Diff contract and comparison models |
| `mirror_diff_text` | First-party diff provider |
| `mirror_monitor` | Monitor contract and monitoring models |
| `mirror_monitor_memory` | First-party monitor provider |
| `mirror_normalize` | Normalization contract and text canonicalization models |
| `mirror_normalize_text` | First-party normalization provider |
| `mirror_enrich` | Enrichment contract and derived metadata models |
| `mirror_enrich_text` | First-party enrichment provider |
| `mirror_dedup` | Deduplication contract and duplicate-resolution models |
| `mirror_dedup_hash` | First-party hash deduplication provider |
| `mirror_provenance` | Provenance contract and resource-envelope models |
| `mirror_provenance_resource` | First-party provenance provider |
| `mirror_compliance` | Compliance contract and policy-check models |
| `mirror_compliance_rules` | First-party compliance provider |
| `mirror_chunk` | Chunking contract and chunk models |
| `mirror_chunk_text` | First-party chunking provider |
| `mirror_embedding` | Embedding contract and vector models |
| `mirror_embedding_hash` | First-party hash embedding provider |
| `mirror_vectorstore` | Vector store contract and query models |
| `mirror_vectorstore_memory` | First-party in-memory vector store provider |
| `mirror_retrieval` | Retrieval contract and ranked-match models |
| `mirror_retrieval_memory` | First-party in-memory retrieval provider |

## How to think about them

A capability package should answer one question only:

> What does this domain mean?

A provider package should answer one question only:

> How do I implement that domain?

`mirror_core` answers the framework question:

> How do all of these pieces run together safely?

That is the separation Mirror follows now.


> Planned control-plane work is documented in ADR-0017 and ADR-0020 through ADR-0023. This repository snapshot does not ship a `mirror_control_django` package.

> The knowledge-infrastructure slice (normalization, enrichment, chunking, deduplication, embeddings, vector storage, retrieval, provenance, and compliance) now ships in the repository snapshot. Remaining provider-specific work is tracked in `docs/FUTURE.md` and ADR-0026.

## Migration note

This repository snapshot still contains the canonical manifest extension model. The canonical direction is the core extension path, and the migration audit is tracked in the roadmap and implementation notes.
