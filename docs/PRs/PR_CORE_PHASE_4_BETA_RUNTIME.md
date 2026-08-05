# PR: Phase four beta runtime

## Problem

Alpha proved the architecture. Beta must prove that Mirror can run real workloads: crawls that persist URLs, scheduled jobs, worker backends, and durable metadata storage.

## Decision

Add beta runtime features in the smallest production-shaped way:

- crawler persistence for discovered URLs and fetched results;
- worker backend contracts with SQLite as the local backend;
- scheduler contracts for recurring work;
- metadata and blob storage boundaries;
- documentation for the bootstrap files that keep the workspace importable;
- user-facing tutorials for crawling and scheduling.

## What changed

- Added beta-level contract docs and ADRs.
- Added crawling, scheduling, storage, and worker concepts.
- Added reference pages for the new runtime pieces.
- Added tutorials for crawling and scheduled crawling.
- Explained the root-level `conftest.py` and `sitecustomize.py` bootstrap helpers.

## Validation

- The runtime is covered by tests.
- The docs describe the crawl/scheduler/storage/worker story.

## Deferred

- Django control plane integration;
- Celery and Redis worker backends;
- advanced SaaS admin features.
