# Distributed reference

## Packages

### `mirror-worker-postgres`

Implements the durable WorkerBackend and related stores with PostgreSQL.

### `mirror-execution-celery`

Implements the Celery execution mechanism. Redis is Celery's broker.

### `mirror-crawl-scrapy`

Implements the Crawl capability using Scrapy. It is a provider, not part of the
worker runtime.

## Environment

```text
MIRROR_POSTGRES_DSN
MIRROR_CELERY_BROKER_URL
MIRROR_WORKER_ID
```

## Execution classes

`default`, `io`, `cpu`, and `gpu` are infrastructure classes. The architecture
does not define queues for individual capabilities.
