# Worker Contract

Workers define how runs are accepted, claimed, checkpointed, completed, and resumed.

## Core contracts

- `WorkerBackend`
- `ExecutionStore`
- `CheckpointStore`
- `ArtifactStore`
- `LeaseManager`

## Alpha expectations

The frozen alpha should include local implementations for development and tests.
Distributed backends are intentionally deferred.

## Why the contract exists

The worker contract lets Mirror grow from a single-process runtime into a distributed system later without changing the application API.

## What belongs in beta

- Redis-backed queues
- cluster scheduling
- remote worker pools
- multi-host lease coordination
- SaaS worker orchestration


## Beta backends

The beta phase adds the SQLite worker backend, then the production Celery/Redis
backend. The control plane later moves into Django.
