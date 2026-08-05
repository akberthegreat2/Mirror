# ADR 0011 — Checkpoint and durability

## Status
Accepted

## Context
Work must survive process death once durable backends are enabled.

## Decision
Durable state SHALL be persisted through explicit store contracts for
checkpoints, leases, and artifacts. In-memory implementations are allowed only
for development.

## Consequences
The runtime can be resumed after a crash once durable stores are connected.
