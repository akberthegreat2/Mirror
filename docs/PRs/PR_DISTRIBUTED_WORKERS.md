# Distributed Workers

## Delivered

- PostgreSQL durable WorkerBackend and storage implementations.
- Transactional PostgreSQL job claiming with `FOR UPDATE SKIP LOCKED`.
- Durable leases and lease renewal.
- Execution-class routing.
- Celery execution transport using Redis as broker.
- Generic worker task that hands work back to Mirror Core.
- Docker Compose development stack for PostgreSQL, Redis, and a generic worker.
- Live Redis + Celery smoke coverage and PostgreSQL integration tests gated by a
  real `MIRROR_TEST_POSTGRES_DSN`.

## Deliberate boundaries

Celery does not decide retries. Redis is not durable state. Workers do not know
capability-specific business logic. Capability providers remain independently
replaceable.
