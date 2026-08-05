# ADR-0015: crawl persistence

Status: Accepted

## Decision

A crawl MUST be able to persist discovered URLs on user demand.
A crawl MAY also store page bodies in blob storage.

## Reason

The legacy behavior that discarded crawl results was not good enough for SaaS
workflows. The beta path needs durable crawl metadata.
