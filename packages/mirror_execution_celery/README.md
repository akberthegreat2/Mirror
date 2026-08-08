# Mirror Celery Execution

`mirror-execution-celery` is Mirror's Celery execution mechanism. Celery owns
transport and process execution only. Mirror Core owns planning, retries,
timeouts, cancellation, checkpoints, and terminal semantics.

Redis is the Celery broker. PostgreSQL remains the durable worker backend.

## Start a worker

```bash
export MIRROR_POSTGRES_DSN=postgresql://mirror:mirror@localhost:5432/mirror
export MIRROR_CELERY_BROKER_URL=redis://localhost:6379/0
mirror-celery-worker --execution-class default
```

Workers are generic. They consume execution IDs/jobs; they do not contain
capability-specific crawler, scraper, search, or analyzer logic.
