# Celery execution

`mirror-execution-celery` is the execution mechanism. It deliberately contains
very little Mirror business logic.

A Celery task receives a durable job ID:

```text
Celery task
   ↓
PostgresWorkerBackend.claim_job()
   ↓
Mirror Core Application
   ↓
Executor
```

Celery's delivery controls (`acks_late`, worker-loss rejection, and prefetch
configuration) improve delivery safety. They do not replace Mirror's retry
policy.

## Worker classes

Start one generic worker for an execution class:

```bash
mirror-celery-worker --execution-class default
mirror-celery-worker --execution-class io
mirror-celery-worker --execution-class cpu
```

The worker does not contain crawler-specific or scraper-specific code.

## Lease reclamation

A claimed job has a durable PostgreSQL lease. If its worker disappears, the
lease expires. Celery Beat invokes Mirror's `mirror.requeue_expired` task every
15 seconds by default, routing the task to `mirror.reaper`. The task only
requeues expired durable jobs; it does not perform retries or select providers.

Run Beat separately in a local deployment:

```bash
mirror-celery-beat --loglevel INFO
```

Set `MIRROR_REAPER_INTERVAL_SECONDS` to change the schedule. The Docker Compose
stack already includes a Beat service.
