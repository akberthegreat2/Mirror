# ADR-0040: Lease reclamation and durable-store certification

**Status:** Accepted

## Context

Mirror's worker contract promises durable state and recovery after worker
failure. The SQLite checkpoint and dead-letter stores are production-facing
local durability implementations, so their serialization, upsert, ordering,
and replay behavior must be tested directly rather than only through in-memory
implementations.

Lease expiry is also a recovery boundary. A backend may expose
`requeue_expired()`, but the distributed deployment must invoke it without
requiring an operator to manually run a repair command.

## Decision

1. SQLite checkpoint and dead-letter stores receive direct round-trip,
   upsert/order, replay, and reopen tests.
2. Dead-letter listings are newest-first (`created_at DESC`) so operational
   consumers see the most recent failures first.
3. The restricted condition evaluator has direct adversarial regression tests
   covering its supported grammar and rejected Python constructs.
4. The unused `mirror_core.extensions.resolve` duplicate resolver is removed;
   `mirror_core.imports` remains the canonical import-resolution contract.
5. The Celery execution adapter registers a dedicated `mirror.requeue_expired`
   task and a Celery Beat schedule. The task only reclaims expired durable jobs;
   retry policy remains owned by Core.
6. The Docker deployment includes a Beat service so lease reclamation is part
   of the documented distributed deployment rather than an implicit manual
   operation.

## Consequences

The durability contract is exercised at the storage boundary, the condition
sandbox has a permanent security regression suite, and a worker crash can be
recovered automatically by the distributed deployment. Redis remains transport;
PostgreSQL remains the durable source of truth.
