# PR: Phase 4 beta runtime proof

## Summary

This phase adds the first real workload path for Mirror beta:

- crawl capability support for persisted URLs
- metadata and blob storage contracts
- in-memory and SQLite scheduler implementations
- SQLite worker backend
- crawl package and tests
- beta docs and ADRs

## What changed

- introduced `mirror_core.storage`
- introduced `mirror_core.scheduler`
- added `SQLiteWorkerBackend`
- added `mirror_crawl`
- documented the beta contract and runtime proof path

## Tests

- storage round trips
- scheduler round trips
- SQLite worker lifecycle
- crawl persistence
- crawl provider swap over HTTPX and Playwright

## Follow-up

- add a Django control plane
- add Redis and Celery adapters for distributed workers
- add a dedicated dashboard package
