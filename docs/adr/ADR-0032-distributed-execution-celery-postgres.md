# ADR-0032: Distributed execution with Celery, Redis, and PostgreSQL

**Status:** Accepted

## Context

Mirror needs a multi-process and multi-host execution mechanism without moving
execution semantics into infrastructure.

## Decision

Mirror separates four responsibilities:

- Core owns planning, scheduling, retries, timeouts, cancellation, middleware,
  execution state, and worker contracts.
- PostgreSQL implements the durable `WorkerBackend` and durable stores.
- Celery implements the execution mechanism.
- Redis is Celery's broker and ephemeral coordination transport.

Workers are generic and consume execution-class queues such as `mirror.default`,
`mirror.io`, `mirror.cpu`, and `mirror.gpu`. Queues do not identify capabilities.

A job is persisted before it is published. Celery receives an execution ID,
claims that exact job through the durable backend, and runs the canonical Core
Executor. Celery retries are disabled as an execution policy; Mirror owns retry
semantics.

## Consequences

Redis can be lost without losing durable execution state. A worker crash leaves
a PostgreSQL lease that can expire and be reclaimed. PostgreSQL is therefore the
source of truth for job state, checkpoints, artifacts, execution history, and
dead letters.
