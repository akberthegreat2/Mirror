# Worker reference

Mirror's worker layer is split into contracts and local implementations.

## Contracts

- `WorkerBackend`
- `ExecutionStore`
- `CheckpointStore`
- `ArtifactStore`
- `LeaseManager`

## In-memory implementations

- `InlineWorker`
- `InMemoryExecutionStore`
- `InMemoryCheckpointStore`
- `InMemoryArtifactStore`
- `InMemoryLeaseManager`
