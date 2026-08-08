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
