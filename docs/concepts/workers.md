# Workers

Workers are part of the frozen alpha core. They define how jobs are queued,
claimed, checkpointed, completed, and resumed.

## Core contracts

- `WorkerBackend`
- `ExecutionStore`
- `CheckpointStore`
- `ArtifactStore`
- `LeaseManager`

## Alpha implementation

The repository ships an in-memory `InlineWorker` and in-memory stores for
local development and tests.

## Why it matters

The contracts let Mirror grow from one local process to a distributed system
later without changing the application-level API.
