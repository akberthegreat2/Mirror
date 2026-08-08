# ADR-0029 — Distributed execution and Celery worker integration

## Status

Superseded by ADR-0032 (accepted)

## Context

Mirror already has worker contracts and backend implementations. The current architecture can run locally, but production systems need distributed execution, queue visibility, retry coordination, and durable worker backends. Celery and Redis have been discussed as part of that direction, but the integration needs a clearer architectural boundary than "Celery support".

## Decision

Mirror Core SHOULD treat distributed execution as a worker-backend concern.

The core rules are:

- `WorkerBackend` remains the public execution contract;
- local, in-memory, and SQLite backends remain valid implementations;
- Celery is one backend implementation, not a replacement for the worker contract;
- Redis MAY be used for queue coordination, result transport, or cache support where required by the chosen backend;
- Core MUST NOT import Celery directly;
- worker behavior MUST still honor execution state, leases, cancellation, terminal outcomes, and durable-state semantics defined by the runtime contract.

A Celery backend SHOULD integrate with the same plan/run model used by local workers. It SHOULD accept an execution plan or run manifest produced by Core and execute it through the same lifecycle rules as other workers.

The scheduler SHOULD submit work to the worker abstraction rather than to Celery-specific APIs.

## Consequences

- local execution and distributed execution share one contract;
- Celery becomes an implementation detail, not a second runtime;
- worker tests can prove backend interchangeability;
- queue semantics can evolve without changing capability code.

## Non-goals

- building a custom queue engine in Core;
- making Celery the only supported worker backend;
- binding capability packages to Celery APIs;
- moving scheduling ownership out of Core.
