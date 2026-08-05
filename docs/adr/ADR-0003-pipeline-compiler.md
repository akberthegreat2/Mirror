# ADR 0003 — Pipeline compiler

## Status
Accepted

## Context
Runtime behavior must be deterministic. Source pipeline definitions are not the
execution format.

## Decision
Pipelines SHALL be compiled into immutable execution plans before execution.
Runtime MUST not rediscover or reparse the definition while running.

## Consequences
Validation errors occur early and execution becomes predictable.
