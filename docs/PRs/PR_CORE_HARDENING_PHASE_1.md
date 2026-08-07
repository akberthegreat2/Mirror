# PR: Harden the mirror-core planner, execution runtime, and lifecycle

## Summary

This PR completes the first core-hardening milestone before additional capabilities are developed. It makes planning deterministic, execution state isolated per invocation, failures observable, provenance accurate, and Application startup transactional and restartable.

## Why

The package split was structurally correct, but the runtime still had several contradictions:

- capability versions were resolved during planning and then replaced with hardcoded version lookups;
- pipeline input declarations were treated as runtime values;
- the shared Executor stored mutable state for every run;
- abort failures were swallowed by concurrent gather logic;
- step-level providers were modeled but ignored;
- resource provenance pointed at every prior result instead of direct dependencies;
- provider setup failure could leak partial resources;
- Application restart skipped later teardown;
- settings merge was shallow and could corrupt secrets.

## Changes

### Registry and compatibility

- Add semantic version parsing and capability resolution.
- Validate provider version specifiers.
- Resolve compatible providers deterministically.
- Add registry freeze behavior.
- Add packaging as a core dependency.

### Planner

- Introduce immutable CompiledStep and ExecutionPlan models.
- Resolve exact capability/provider manifests once.
- Validate duplicate IDs, bindings, input declarations, ports, and cycles.
- Preserve exact dependencies for provenance and scheduling.

### Executor

- Introduce isolated ExecutionRun state and immutable ExecutionResult.
- Add explicit run outcomes.
- Accept runtime inputs at execution.
- Support concurrent invocations without shared state corruption.
- Propagate abort failures.
- Formalize middleware short-circuit behavior.
- Add a safe minimal condition evaluator.
- Record exact producer and direct-parent provenance.

### Application

- Use AsyncExitStack for rollback-safe startup.
- Register ownership before setup.
- Reset lifecycle state on failure.
- Validate duplicate discovery results.
- Keep startup transactional and restartable.

## Validation

- Core tests pass.
- Planner and executor semantics are covered by tests.
- Application lifecycle behavior is covered by tests.

## Deferred

- distributed workers
- dashboard / Django integration
- durable execution stores
- additional capabilities
