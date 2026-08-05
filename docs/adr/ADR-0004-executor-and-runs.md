# Executor and runs

**Status:** Accepted  
**Date:** 2026-08-05

## Context

The executor must be reusable across runs. Mutable state for one invocation
must not leak into another invocation.

## Decision

Each invocation MUST own an ExecutionRun object. Shared executor state MUST
stay read-only once the plan is compiled. Cancellation and results MUST be scoped
to a run identifier.

## Consequences

Concurrent runs remain isolated and the framework can grow into workers
later without changing the application API.
