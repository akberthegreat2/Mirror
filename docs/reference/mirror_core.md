# mirror_core reference

The `mirror_core` package exports the framework primitives used by every
other Mirror package.

## Public surface

- `Application`
- `MirrorSettings`
- `Pipeline`, `Step`, `RetryPolicy`, `ErrorPolicy`
- `Planner`, `ExecutionPlan`
- `Executor`, `ExecutionRun`, `ExecutionResult`, `RunOutcome`, `StepState`
- `SignalBus`
- `Invocation`, `Middleware`, `MiddlewareChain`
- `ResourceEnvelope`, `ProducerRef`, `BlobReference`
- worker contracts and in-memory stores

The core package deliberately imports no capability-specific package.
