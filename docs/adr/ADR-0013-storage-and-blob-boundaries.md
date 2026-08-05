# ADR 0013 — Storage and blob boundaries

## Status
Accepted

## Context
Mirror needs to separate metadata from large payloads.

## Decision
Metadata SHALL live in the database. Payloads, archives, and large binary
outputs SHALL live in blob storage or filesystem-backed development storage.

## Consequences
Database rows stay lightweight and operational data stays manageable.
