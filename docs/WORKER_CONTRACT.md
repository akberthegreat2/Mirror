# Worker Contract

Workers are how Mirror accepts work, leases it to a runner, records progress,
and stores results.

## Core contracts

- `WorkerBackend` — durable queue/lease lifecycle.
- `ExecutionStore` — completed execution metadata.
- `CheckpointStore` — resumable step state.
- `ArtifactStore` — large or binary artifacts.
- `LeaseManager` — exclusive ownership of one job.

A worker job has an **execution class**. Classes describe infrastructure
requirements, not capabilities. Typical classes are `default`, `io`, `cpu`, and
`gpu`.

## Distributed boundary

Mirror currently provides:

- `InlineWorker` for tests and single-process development;
- `SQLiteWorkerBackend` for durable local workflows;
- `PostgresWorkerBackend` in `mirror-worker-postgres` for distributed durability;
- `Celery` in `mirror-execution-celery` as the execution mechanism;
- Redis as Celery's broker.

The worker transport never owns retry, timeout, fallback, cancellation, or
capability selection. Those remain Core semantics.

## Claiming

Workers claim one job exclusively. PostgreSQL uses transactional row locking
with `FOR UPDATE SKIP LOCKED` and a lease expiry. A dead worker therefore does
not permanently own work.

## Recovery

A job is persisted before it is published to Celery. If a worker dies after
claiming it, the lease expires and the job becomes claimable again. Redis is not
the source of truth.

## Future adapters

Other execution mechanisms may implement the same contract, for example Ray or
Kubernetes, without changing capability packages or Core execution semantics.
