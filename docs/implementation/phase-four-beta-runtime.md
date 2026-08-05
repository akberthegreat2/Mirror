# Phase four: beta runtime

**Status:** In progress.

## Goal

Prove that Mirror can run real workloads: crawl URLs, persist results, schedule
recurring jobs, and store metadata and blobs in durable backends.

## Delivered in this phase

- crawl persistence contract
- scheduler contract
- SQLite worker backend
- metadata and blob storage boundaries
- documentation for the bootstrap files that keep the workspace importable
- user-facing tutorials for crawling and scheduling

## Deferred to later phases

- Redis and Celery production backends
- cluster-scale execution
- SaaS admin polish
