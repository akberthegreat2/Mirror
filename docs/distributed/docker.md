# Docker development environment

Mirror's root `docker-compose.yml` is a development deployment, not a
production Kubernetes specification.

It contains four services:

```text
postgres  durable state
redis     Celery broker
worker    generic Mirror worker
beat      lease-reclamation scheduler
```

## Start

```bash
docker compose up --build -d
```

## Observe

```bash
docker compose ps
docker compose logs -f worker
docker compose logs -f beat
```

## Reset

```bash
docker compose down -v
```

The `-v` flag deletes the development PostgreSQL volume. Do not use it against a
production deployment.

## Configuration

The worker receives:

```text
MIRROR_POSTGRES_DSN
MIRROR_CELERY_BROKER_URL
MIRROR_WORKER_ID
```

No database credentials or broker addresses are hardcoded into Core.
