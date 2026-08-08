# Mirror distributed runtime handover

## What changed

This snapshot adds the first real distributed execution path while preserving
Core ownership boundaries.

### Core

- Worker jobs now carry an execution class.
- Workers can claim one specific job or the next job in a class.
- Scheduler records expose execution classes while retaining `queue_name` for
  compatibility.
- Application accepts Core-owned metadata/checkpoint/dead-letter stores.
- Application can execute a serialized worker job through the normal Executor.
- Plan fingerprints include resolved provider identity so distributed workers
  can verify that the compiled provider selection is stable.

### PostgreSQL

`mirror-worker-postgres` provides:

- durable worker jobs;
- transactional `FOR UPDATE SKIP LOCKED` claiming;
- leases and heartbeat renewal;
- execution history;
- checkpoints;
- artifacts;
- dead letters;
- metadata.

PostgreSQL is the durable source of truth.

### Celery + Redis

`mirror-execution-celery` provides:

- real Celery application configuration;
- Redis broker routing;
- execution-class queues;
- generic worker task;
- automatic `mirror.requeue_expired` lease-reclamation task;
- Celery Beat scheduling on the dedicated `mirror.reaper` queue;
- worker bootstrap command;
- Beat bootstrap command;
- pipeline submission command.

Celery does not own Mirror retry semantics.

### Crawl provider

`mirror-crawl-scrapy` provides a real Crawl provider backed by Scrapy. The
worker layer contains no crawler implementation.

### Deployment

The repository now includes:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- GitHub CI configuration for PostgreSQL + Redis integration.

## Tests

The repository test suite passed:

```text
291 passed, 5 skipped
```

The five skipped tests are explicitly marked external-integration tests. No
Redis or PostgreSQL shim is used to turn those tests green.

The uploaded `postgresql-wheel` artifact was importable as the Python
`postgresql` package, but it is a PyPy 3.8-oriented wheel and does not provide a
usable PostgreSQL server binary for this CPython 3.13 sandbox. It was therefore
not used as a fake server.

## Local distributed run

```bash
docker compose up --build -d
docker compose ps
```

Then submit a pipeline:

```bash
export MIRROR_POSTGRES_DSN='postgresql://mirror:mirror@localhost:5432/mirror'
export MIRROR_CELERY_BROKER_URL='redis://localhost:6379/0'
mirror-celery-submit crawl.json --inputs '{"url":"https://example.com"}' --execution-class io
```

The worker consumes the durable job ID and hands the pipeline back to Core.

## Architectural review

The distributed path was checked against `docs/ARCHITECTURE.md`:

- Core remains capability-agnostic.
- Celery does not implement execution semantics.
- Redis is not durable state.
- PostgreSQL owns durable worker state.
- Workers are generic.
- Queues are execution-class based, not capability based.
- Providers remain separate extensions.
- Scrapy is integrated as a provider rather than replaced with a home-grown
  crawler.
- No Redis/PostgreSQL shim is included.
- SQLite durable stores have direct round-trip/reopen tests.
- The condition evaluator has direct adversarial security regression tests.
- The duplicate unused extension resolver was removed.
- Lease reclamation is automatically scheduled by Celery Beat in the distributed
  deployment.

The remaining external certification gate is a live PostgreSQL/Redis deployment
test against real services. The repository's CI configuration is prepared to
run those integration tests when the services are available.
