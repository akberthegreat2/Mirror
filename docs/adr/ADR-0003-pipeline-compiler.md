# Pipeline compiler

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Pipelines are authored as declarative DAGs, but the executor must not run raw
user definitions. The framework needs a compilation step that validates and
orders the graph.

## Decision

The planner SHALL convert a pipeline into an immutable execution plan before
execution. The compiler MUST resolve capability versions, provider selection,
port bindings, conditions, and middleware policy before the run starts.

## Consequences

The executor becomes simpler and runtime failures become easier to reason
about.
