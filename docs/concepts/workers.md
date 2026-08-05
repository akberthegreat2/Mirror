# Workers

Workers run the jobs that Mirror schedules.

## What a worker does

A worker:

- claims work
- runs a pipeline or task
- records heartbeats
- marks the job as done or failed
- keeps state separate from the caller

## Core contracts

- `WorkerBackend`
- `ExecutionStore`
- `CheckpointStore`
- `ArtifactStore`
- `LeaseManager`

## Local beta implementations

Mirror ships:

- `InlineWorker` for tests and quick starts
- `SQLiteWorkerBackend` for one-machine beta setups
- in-memory stores for development

## Why it matters

A crawl or monitor is only useful if Mirror can run it again later.
Workers are the piece that makes that possible.
