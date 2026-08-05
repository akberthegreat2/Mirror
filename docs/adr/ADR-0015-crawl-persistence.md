# ADR 0015 — Crawl persistence

## Status
Accepted

## Context
A crawler that does not remember discovered URLs is not useful for SaaS.

## Decision
A crawler SHALL be able to persist discovered URLs and fetched results when the
pipeline or settings request it.

## Consequences
Crawling becomes useful for monitoring, archiving, and product workflows.
