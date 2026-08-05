# Execution

A Mirror pipeline describes the work you want to do. Mirror compiles that
pipeline into a plan, then executes the plan one run at a time.

## The main pieces

- `Pipeline` — what the user writes
- `ExecutionPlan` — what Mirror compiles
- `ExecutionRun` — state for one run
- `Executor` — the reusable engine that runs the plan

## What happens during a run

1. Mirror loads the project settings.
2. Mirror resolves the selected capability and provider.
3. Mirror checks the pipeline for missing inputs and invalid links.
4. Mirror runs the compiled plan.
5. Mirror records the results and the final outcome.

## Inputs

Pipeline inputs describe what the pipeline expects.

Runtime inputs are the actual values passed by the caller when the run starts.

That separation keeps the pipeline reusable.
