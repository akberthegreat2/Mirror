# ADR 0004 — Executor and execution run

## Status
Accepted

## Context
The executor needs to be reusable, while run state must remain isolated.

## Decision
Executor SHALL be reusable. Per-invocation mutable state SHALL live in
ExecutionRun, not on the shared executor object.

## Consequences
Concurrent runs stay isolated and cancellation targets a single run.
