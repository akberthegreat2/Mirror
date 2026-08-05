# Execution

Mirror compiles a pipeline into an execution plan, then executes that plan
through an isolated `ExecutionRun`.

## Main objects

- `Pipeline`
- `Step`
- `ExecutionPlan`
- `ExecutionRun`
- `Executor`

## Lifecycle

1. The application bootstraps settings, registry, middleware, and signals.
2. The planner validates the DAG and resolves capabilities/providers.
3. The executor runs the compiled plan with bounded concurrency.
4. The run finishes with a terminal outcome and a result envelope per step.

## Runtime inputs

Pipeline input declarations are not runtime values. The caller passes runtime
inputs at execution time.
