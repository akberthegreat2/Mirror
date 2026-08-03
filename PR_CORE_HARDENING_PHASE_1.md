# PR: Harden the mirror-core planner, execution runtime, and lifecycle

## Summary

This PR completes the first core-hardening milestone before additional capabilities are developed. It makes planning deterministic, execution state isolated per invocation, failures observable, provenance accurate, and Application startup transactional and restartable.

## Why

The package split was structurally correct, but the runtime still had several contradictions:

- capability versions were resolved during planning and then replaced with hardcoded `"1.0"` lookups;
- pipeline input declarations were treated as runtime values;
- the shared Executor stored mutable state for every run;
- abort failures were swallowed by `asyncio.gather(return_exceptions=True)`;
- step-level providers were modeled but ignored;
- every previous result was recorded as a resource parent;
- provider setup failure could leak partial resources;
- Application restart skipped later teardown;
- settings merge was shallow and could corrupt secrets.

## Changes

### Registry and compatibility

- Add semantic version parsing and capability resolution.
- Validate provider version specifiers.
- Resolve compatible providers deterministically.
- Add registry freeze behavior.
- Add `packaging` as a core dependency.

### Planner

- Introduce immutable `CompiledStep` and `ExecutionPlan` models.
- Resolve exact capability/provider descriptors once.
- Validate duplicate IDs, bindings, input declarations, ports, and cycles.
- Preserve exact dependencies for provenance and scheduling.

### Executor

- Introduce isolated `ExecutionRun` state and immutable `ExecutionResult`.
- Add explicit run outcomes.
- Accept runtime inputs at execution.
- Support concurrent invocations without shared state corruption.
- Propagate abort failures.
- Formalize middleware short-circuit behavior.
- Add a safe minimal condition evaluator.
- Record exact producer and direct-parent provenance.

### Application

- Use `AsyncExitStack` for rollback-safe startup.
- Reject discovery duplicates.
- Freeze registries before instantiation.
- Validate provider protocols at startup.
- Key provider instances by capability and provider.
- Support clean restart of the same Application instance.
- Use configured concurrency.

### Settings

- Add `max_concurrency` and middleware settings.
- Deep-merge nested configuration.
- Preserve secrets internally while redacting public dumps.
- Normalize configuration file errors.

### Tests and docs

- Replace implementation-coupled executor tests with run/outcome contracts.
- Add semantic version, runtime input, provenance, short-circuit, concurrent-run, rollback, restart, and deep-merge tests.
- Add the core package README and implementation record.

## Validation

```text
62 passed in 1.30s
```

All available package tests passed except the optional WARC test package, which could not be executed because `warcio` is unavailable in the environment.

Ruff and mypy were not installed in the execution environment and remain mandatory CI checks before merge.

## Breaking changes

- `Executor` no longer accepts a Registry; plans carry all resolved descriptors.
- `Executor.set_producer()` is removed; producer identity is generated per step.
- Runtime pipeline values must be passed to `execute()`, `execute_run()`, or `Application.run_pipeline(inputs=...)`.
- Abort failures now raise `ExecutionError` from `execute()` instead of silently returning partial results.

These changes are intentional for the v0.1 alpha architecture.

## Deferred follow-ups

1. Namespace-based entry-point discovery.
2. Middleware compilation by capability and step.
3. Full error-policy compiler.
4. Durable execution/checkpoint contracts.
5. Resource schema registry and blob serialization.
6. Dynamic interfaces and CLI command contributions.
