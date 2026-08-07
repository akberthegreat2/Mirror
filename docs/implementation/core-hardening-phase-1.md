# Core Hardening Phase 1

**Status:** Implemented
**Scope:** `mirror-core` only
**Architecture references:** Planner, Executor, Settings, Lifecycle, Resource Model

## Objective

Make the core runtime truthful before more capabilities are added. This phase removes runtime ambiguity between planning and execution and establishes isolated execution state, resolved component identities, explicit runtime inputs, accurate provenance, and transactional lifecycle behavior.

## Implemented contracts

### Descriptor registry

- Capability versions are parsed and ordered with `packaging.version.Version`.
- Provider compatibility is validated with `packaging.specifiers.SpecifierSet`.
- The planner resolves the exact capability and provider once.
- Registries may be frozen after startup compilation.

### Pipeline planning

`Planner.plan()` now produces immutable `CompiledStep` objects. Each compiled step contains:

- the original step definition;
- the resolved capability descriptor and API version;
- the resolved provider descriptor;
- exact data dependencies.

The plan validates:

- duplicate step identifiers;
- pipeline input declarations;
- source step and output references;
- request/result field compatibility where type information exists;
- provider compatibility;
- graph acyclicity.

Runtime values are no longer taken from `Pipeline.inputs`. `Pipeline.inputs` declares accepted names; values are supplied to execution.

### Execution runtime

`Executor` is reusable and owns no per-run mutable state. Each invocation creates an `ExecutionRun` containing:

- a unique run ID;
- runtime input values;
- step states;
- results;
- errors;
- cancellation state.

`ExecutionResult` classifies terminal outcomes as:

- `SUCCEEDED`;
- `FAILED`;
- `PARTIALLY_SUCCEEDED`;
- `CANCELLED`.

Abort failures are no longer swallowed. `Executor.execute()` raises `ExecutionError`; `execute_run()` returns the complete terminal state for interfaces that need structured failure reporting.

### Resource provenance

Every output envelope records the actual:

- capability and API version;
- provider and optional provider version;
- step identifier;
- plan configuration fingerprint;
- direct parent resources only.

Resource envelopes are frozen, and their `parents`/`metadata` containers are normalized so provenance cannot be mutated in-place after creation.

Parallel or unrelated outputs are not incorrectly recorded as parents.

### Application lifecycle

Application startup now uses `AsyncExitStack`:

- teardown is registered before setup starts;
- a provider that partially initializes and then raises is still torn down;
- descriptors are rejected when discovery reports duplicates;
- registries are frozen before component construction;
- runtime state is recreated cleanly after shutdown;
- the same `Application` instance supports a full start/shutdown/restart cycle.

Provider instances are keyed by `(capability, provider)`, allowing future pipelines to select different providers for the same capability.

### Settings

- `max_concurrency` is configurable.
- settings merging is recursive rather than shallow;
- `SecretStr` values remain intact during internal merges;
- public dumps remain redacted;
- YAML is treated as an optional dependency and reports a core configuration error when unavailable.

## Deliberately deferred

This PR does not claim to complete:

- namespace-based discovery groups;
- retry semantics in the executor;
- durable execution stores and checkpoints;
- schema registry and distributed resource deserialization;
- distributed execution backends;
- CLI command discovery;
- WARC provider hardening.

Those are separate architectural milestones and should not be mixed into this core runtime PR.

## Validation

Executed in the supplied repository snapshot:

```text
62 passed in 1.30s
```

The test run covered all packages except `mirror_archive_warc`, whose optional `warcio` dependency is unavailable in the execution environment.

`compileall` and AST parsing completed successfully for `mirror_core`.

Ruff and mypy were not available in the execution environment; CI must run them before merge.
