# Execution Semantics

Mirror compiles a pipeline into an execution plan, then runs that plan through an isolated execution run.

## Core terms

- **Pipeline**: the declarative DAG authored by a user.
- **ExecutionPlan**: the compiled, validated plan that the runtime executes.
- **ExecutionRun**: per-run state for one invocation.
- **PipelineCompiler**: the owner of raw pipeline parsing and validation.
- **Executor**: the reusable engine that runs compiled plans.

## Terminal outcomes

The runtime should surface a terminal status for every run:

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `PARTIALLY_SUCCEEDED`

`RunOutcome.PARTIAL` remains a temporary compatibility alias for older callers, but new code should use `PARTIALLY_SUCCEEDED`.

A finished run does not automatically mean success; the terminal status must say so.

## Runtime inputs

Pipeline input declarations are schema, not values. Callers provide runtime inputs at execution time.

## Compilation responsibilities

The compiler and planner should resolve these before execution starts:

- capability version
- provider selection
- port bindings
- conditions
- middleware chain
- retry and timeout policy; fallback providers are supported at the step level through the compiled plan
- typed dependencies

Execution should not rediscover or re-resolve those values.

`ExecutionContext` captures a frozen per-run snapshot, `CapabilityContext`
subdivides that snapshot for a specific capability invocation, and the
`PipelineCompiler` ensures the raw definition is normalized before the planner
resolves runtime identities.

## Concurrency and isolation

Each run must own its own state.
Concurrent runs must not share mutable execution state.
`ExecutionContext`, `CapabilityContext`, and `ResourceEnvelope` are read-only snapshots once constructed, and middleware receives the same immutable runtime facts that the executor sees.

## Failure handling

Execution should distinguish between:

- abort
- continue
- skip

Fallback can substitute another provider when a compiled step declares fallback providers; alternate step or pipeline fallback remains outside the current runtime implementation.

A terminal failure must propagate from execution and must not be hidden behind a generic finished event.

## Note on beta runtime

The beta runtime will add crawler persistence, scheduler support, and durable
worker backends. Those pieces are documented in `BETA_CONTRACT.md` and the
phase-four implementation note.
