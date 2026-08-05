# ADR 0019 — Metadata store

## Status
Accepted

## Context
Mirror needs a canonical database strategy for metadata.

## Decision
PostgreSQL SHALL be the canonical production database. SQLite SHALL be the
canonical development database. MySQL MAY be supported as an alternative.

## Consequences
Database choice remains modular without leaking into runtime semantics.
