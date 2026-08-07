# Mirror Beta Contract

This document defines the next release stage after the frozen alpha. Beta is the
first stage where Mirror is expected to support real SaaS workloads, not just
prove its architecture.

## Beta means

Mirror beta must provide:

- crawl persistence for discovered URLs and fetched results;
- worker backends suitable for local development and production queues;
- a Django control plane for users, auth, and admin operations;
- docs, ADRs, tests, and PR notes for every user-facing promise.

Scheduler support has already graduated into the stable core package (`mirror_core.scheduler`). Metadata storage now lives in `mirror_core.metadata` and is re-exported from `mirror_core.storage` for compatibility; blob storage remains in `mirror_core.storage`.

## Beta runtime guarantees

- Crawlers MUST save discovered URLs when configured to do so.
- Workers MUST be able to resume work from persisted state.
- Scheduler jobs MUST be repeatable and observable.
- Metadata and blob storage MUST use the stable core backends documented in
  `mirror_core.metadata` and `mirror_core.storage`.
- Redis MAY be used for cache, queue, and lease coordination.
- Django admin MUST be able to read and manage stored metadata.

## Deferred to later releases

- cluster-scale distributed execution
- advanced SaaS tenancy and billing
- higher-level search products
- integration with multiple external task systems beyond the supported beta
  backends
