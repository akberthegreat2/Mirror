# ADR-0027 — Trusted execution pipeline

## Status

Accepted

## Context

Mirror already has a DAG compiler, a planner, an executor, immutable resource envelopes, middleware, and execution runs. That is enough structure to support a trusted execution pipeline, but the enterprise semantics of that pipeline still need a formal contract.

The goal is not to add a second runtime. The goal is to make the current runtime predictable, auditable, and testable under production conditions. The named `PipelineCompiler` boundary now owns raw-definition parsing and validation before planning begins.

## Decision

Mirror Core SHOULD treat the pipeline as a trusted execution system with one owner for each concern:

- `PipelineCompiler` owns parsing and schema validation of raw pipeline definitions before planning begins.
- `Planner` owns DAG validation, dependency ordering, type compatibility checks, provider selection, and policy binding.
- `Executor` owns runtime execution only.
- `ExecutionRun` owns mutable per-run state.
- `ExecutionPlan.steps` is a read-only mapping after compilation.
- `ExecutionPlan.dependencies` is exposed as an immutable snapshot.
- `ResourceEnvelope` owns provenance and MUST remain immutable after creation.

The planner MAY bind middleware, retry policy, timeout policy, and cancellation policy into an execution plan. The executor MUST NOT rediscover components, rebuild plans, or select providers.

The runtime SHOULD support the following semantics as first-class contracts:

- deterministic plan generation from the same inputs;
- cycle detection before execution begins;
- typed step inputs and outputs;
- explicit execution ordering;
- short-circuit-capable middleware;
- observable signals that do not control execution;
- per-run isolation of mutable state;
- clear terminal outcomes for success, partial success, failure, and cancellation;
- provenance-bearing resources that preserve lineage across steps.

Future policy families such as fallback, checkpoint/replay, and compensation remain reserved for later ADRs. They are part of the trusted-pipeline direction, but they are not a requirement for this proposal to be valid.

## Consequences

- execution becomes easier to reason about and test;
- compile-time validation is favored over runtime discovery;
- middleware stays a control surface, not a second planner;
- resource lineage remains stable across the entire run;
- compiled plans remain deeply immutable so the executor cannot be mutated after planning;
- failure handling can be expanded later without changing ownership.

## Non-goals

- introducing a second planner;
- letting the executor perform discovery;
- allowing signals to control execution;
- implementing fallback, replay, or compensation immediately;
- turning the pipeline into an AI-specific runtime.
