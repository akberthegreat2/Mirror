# Worker Contract

Workers are how Mirror accepts work, leases it to a runner, records progress,
and stores results.

## Core contracts

- `WorkerBackend` — the queue/lease transport.
- `ExecutionStore` — where completed runs are recorded.
- `CheckpointStore` — where resumable step state is saved.
- `ArtifactStore` — where large files and blobs are stored.
- `LeaseManager` — how one worker keeps exclusive access to a job.

## What the local runtime supports today

Mirror ships two local worker backends:

- `InlineWorker` for tests and single-process development.
- `SQLiteWorkerBackend` for durable local workflows.

These backends are intentionally small, but they are real. They let the test
suite and the command line exercise the same lifecycle that a distributed queue
will later use: submit, claim, heartbeat, complete, fail.

## Why the contract exists

The worker contract keeps the runtime honest. A future Redis or Celery adapter
can plug in without changing how the application talks to workers.

## Future adapters

Later phases may add:

- Redis-backed queues
- remote worker pools
- multi-host lease coordination
- cluster scheduling
- SaaS worker orchestration
