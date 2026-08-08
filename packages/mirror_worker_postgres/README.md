# Mirror PostgreSQL Worker Backend

`mirror-worker-postgres` is the durable distributed worker backend for Mirror.
It stores jobs, execution history, checkpoints, artifacts, leases, metadata,
and dead letters in PostgreSQL.

Redis is deliberately not used as durable state. Celery/Redis is the execution
transport; PostgreSQL is the durable source of truth.

## Configuration

Set `MIRROR_POSTGRES_DSN`, for example:

```text
postgresql://mirror:mirror@localhost:5432/mirror
```

The backend applies its versioned SQL migrations when started.

## Production rule

Do not replace this backend with an ad-hoc database wrapper. It implements the
published Core worker and storage contracts so the same execution semantics can
run inline, locally, or through Celery.
