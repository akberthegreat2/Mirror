# Distributed execution

Mirror's distributed runtime has three infrastructure pieces:

```text
PostgreSQL  -> durable state
Redis       -> Celery broker / ephemeral coordination
Celery      -> process and host execution
```

Core remains the authority for execution semantics.

## Start locally

```bash
docker compose up --build
```

Check services:

```bash
docker compose ps
```

Stop them:

```bash
docker compose down
```

Remove the development database too:

```bash
docker compose down -v
```

## Execution classes

Workers consume infrastructure classes rather than capability queues:

- `default` — general work
- `io` — I/O-heavy work
- `cpu` — CPU-heavy work
- `gpu` — GPU-enabled work

The scheduler selects the class. A crawler is not assigned a `crawl` queue.

## Durability model

PostgreSQL is authoritative. Redis may disappear and be restarted without
losing durable jobs. A worker lease expires after a worker failure, allowing a
new worker to reclaim the job.

## Production rule

Do not put capability-specific logic in the Celery worker. The worker receives
an execution job and calls Core. Providers remain ordinary Mirror extensions.
