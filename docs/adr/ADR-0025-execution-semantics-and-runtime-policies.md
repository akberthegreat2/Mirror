# ADR-0025 — Execution semantics and runtime policies

## Status

Accepted

## Context

Mirror already compiles declarative pipelines into immutable execution plans and
runs them through isolated execution runs. The current runtime has three
important ownership rules that must stay stable:

1. `ExecutionRun` owns the mutable state for one invocation.
2. `ResourceEnvelope` owns provenance and stays immutable after creation.
3. Middleware and signals are cross-cutting contracts, not places to hide
   planning or discovery logic.

The current runtime already ships retry, timeout, and cancellation behavior.
ExecutionPolicy now makes those step-level decisions explicit in the runtime
contract. Fallback, checkpoint/replay, and compensation are now observable core
runtime hooks; their semantics remain owned by Core.

## Decision

Mirror Core SHALL own execution policy definitions. The runtime contract SHALL
treat the following as core-owned policy concerns:

- retry;
- timeout;
- cancellation;
- fallback;
- checkpointing;
- resume/replay;
- compensation.

The current repository snapshot implements retry, timeout, cancellation,
fallback, checkpoint/replay, and compensation hooks in the core runtime.
The remaining policy families must still be added through ADRs before they
become part of the public contract.

Middleware MAY observe, transform, annotate, or short-circuit work. Middleware
MUST NOT rediscover components, recompile pipelines, or invent new provider
resolution rules.

Signals MUST observe runtime facts only. Signals MUST NOT control execution or
be the only place a guarantee exists.

Current middleware scopes are limited to:

- global/application middleware;
- capability middleware.

Future step-level or pipeline-level middleware scopes may be introduced later,
but only through an ADR that updates the runtime contract.

`ExecutionRun` remains the unit of mutable per-run state. `ExecutionContext`
and `CapabilityContext` are now part of the runtime contract, and they preserve
the same ownership model. `ExecutionContext`, `CapabilityContext`, and `ResourceEnvelope` are treated as immutable snapshots after construction, and middleware/signal ordering is deterministic under the executor.

## Consequences

- the executor stays focused on running plans;
- policy changes do not leak into capability packages;
- middleware remains a control surface, not a second planner;
- signals remain observational and testable;
- the runtime can grow new policies later without reassigning ownership.

## Non-goals

- introducing a second planner;
- moving discovery into middleware;
- making signals control execution;
