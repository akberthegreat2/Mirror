# Checkpoint and durability

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror will eventually need durable execution. The first alpha does not need
a distributed system, but it does need a shape that can grow into one.

## Decision

The core SHALL define checkpoint and durability contracts even when the first
implementation is local. Persisted execution state, checkpoint records, and blob
references belong in the contract. Actual database and object-store backends MAY
arrive later.

## Consequences

The framework keeps its future options open without inventing infrastructure
too early.
