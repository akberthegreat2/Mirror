# PostgreSQL durable state

`mirror-worker-postgres` is the distributed persistence implementation.

## Tables

The package owns versioned SQL migrations for:

- `mirror_jobs`
- `mirror_leases`
- `mirror_worker_heartbeats`
- `mirror_execution_runs`
- `mirror_checkpoints`
- `mirror_artifacts`
- `mirror_dead_letters`
- `mirror_metadata`

## Why PostgreSQL is authoritative

A queue broker is optimized for message delivery. It is not the right place for
Mirror's durable execution history. PostgreSQL gives the framework a durable,
queryable record independent of Redis availability.

## Connection

```text
MIRROR_POSTGRES_DSN=postgresql://mirror:mirror@localhost:5432/mirror
```

The backend applies the initial schema migration on startup. Future schema
changes must be versioned migrations and documented through an ADR when they
change architectural guarantees.
