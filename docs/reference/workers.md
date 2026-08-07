# Worker reference

Mirror's worker layer is split into contracts, runtime helpers, and local implementations.

## Contracts

- `WorkerBackend`
- `ExecutionStore`
- `CheckpointStore`
- `ArtifactStore`
- `LeaseManager`
- `DeadLetterQueue`

## Runtime helpers

- `WorkerRuntime`
- `SQLiteExecutionStore`
- `SQLiteLeaseManager`

## In-memory implementations

- `InlineWorker`
- `InMemoryExecutionStore`
- `InMemoryCheckpointStore`
- `InMemoryArtifactStore`
- `InMemoryLeaseManager`
- `InMemoryDeadLetterQueue`

## SQLite implementations

- `SQLiteWorkerBackend`
- `SQLiteDeadLetterQueue`
- `SQLiteCheckpointStore`
