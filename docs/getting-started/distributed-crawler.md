# Run a distributed crawler

This guide explains the smallest useful distributed Mirror deployment.

## 1. Start infrastructure

From the repository root:

```bash
docker compose up --build -d
```

Check that PostgreSQL, Redis, and the worker are healthy:

```bash
docker compose ps
docker compose logs -f worker
```

## 2. Understand the roles

**PostgreSQL** stores durable jobs and execution history.

**Redis** carries Celery messages. It is not the durable queue of record.

**Celery** starts work on worker processes.

**Mirror Core** plans and executes the pipeline.

**A crawler provider** implements the Crawl capability. The worker itself does
not contain crawler code.

## 3. Define a crawl pipeline

A distributed job contains a normal Mirror pipeline plus runtime inputs. The
worker receives that job and hands it back to Core. This means the exact same
pipeline can run inline during development and through Celery in production.

Conceptually:

```python
Pipeline(
    id="site-crawl",
    inputs={"url": "url"},
    steps=[
        Step(
            id="crawl",
            capability="crawl",
            provider="local",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    ],
)
```

The provider is part of the compiled plan. It is never selected by Celery.

## 4. Choose the execution class

Use infrastructure classes, not capability names:

```text
default
io
cpu
gpu
```

For example, an I/O-heavy crawl can be scheduled as `io`. The corresponding
Celery queue is `mirror.io`.

## 5. Production crawler provider

For real crawling, install `mirror-crawl-scrapy`. It uses the established Scrapy
crawler engine; Mirror only supplies the capability contract and provider
adapter.

```bash
pip install mirror-crawl mirror-crawl-scrapy
```

Select the `scrapy` provider in the pipeline. The `mirror-crawl-local` provider
remains useful for deterministic local tests, but it is not the production
crawler engine.

## 6. Recovery

If a worker dies after claiming a job:

1. PostgreSQL keeps the job in `running` state with its lease.
2. The lease eventually expires.
3. The backend makes the job claimable again.
4. Another generic worker can claim it.
5. Core resumes from the durable checkpoint when the execution policy allows it.

Redis loss does not erase PostgreSQL state.

## 7. Submit a distributed pipeline

Create `crawl.json` containing a normal Mirror pipeline definition. Then submit
it to PostgreSQL and publish its execution ID through Celery:

```bash
export MIRROR_POSTGRES_DSN='postgresql://mirror:mirror@localhost:5432/mirror'
export MIRROR_CELERY_BROKER_URL='redis://localhost:6379/0'

mirror-celery-submit crawl.json \
  --inputs '{"url":"https://example.com"}' \
  --execution-class io
```

The command prints the durable job ID. The worker consumes that ID and Core
executes the pipeline using the provider selected in the compiled plan.
