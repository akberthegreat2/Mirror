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

Step `on_error` policies have distinct runtime semantics:

- **abort**: fail the execution and cancel pending work.
- **continue**: record the failed step and allow independent branches to continue; dependents that require the failed result remain unrunnable and are skipped during finalization.
- **skip**: record the failed step and immediately mark its transitive dependents as skipped. Independent branches continue.
- **fallback**: try the compiled fallback providers first. If all fallback providers fail, the failure is recorded and the run continues only where the failed step's result is not required.

Fallback can substitute another provider when a compiled step declares fallback providers; alternate step or pipeline fallback remains outside the current runtime implementation.

### Retry and timeout ownership

Step-level `retry` and `timeout` fields are **execution policy** and are enforced by Core's `PolicyInvoker`. The built-in `RetryMiddleware` and `TimeoutMiddleware` are separate middleware concerns and may be used when an application explicitly wants middleware-level retry or timeout behavior.

Applications should not configure both mechanisms for the same invocation unless deliberate composition is intended. If both are enabled, their effects compose rather than replace one another; middleware retry can repeat an invocation that Core itself is also retrying, and middleware timeout can bound each individual middleware attempt while Core's timeout bounds the policy invocation.

The worker transport does not retry or timeout execution on its own.

A terminal failure must propagate from execution and must not be hidden behind a generic finished event.

## Note on beta runtime

The beta runtime will add crawler persistence, scheduler support, and durable
worker backends. Those pieces are documented in `BETA_CONTRACT.md` and the
phase-four implementation note.
