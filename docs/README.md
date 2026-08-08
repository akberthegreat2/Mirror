# Mirror documentation

Mirror keeps **architecture decisions**, **implementation notes**, and
**educational documentation** separate.

## Start here

- `ARCHITECTURE.md` — constitutional rules. Read this before changing Core.
- `getting-started/` — install Mirror and run your first workflow.
- `concepts/` — understand Core, capabilities, providers, pipelines, and workers.
- `tutorials/` — practical examples.
- `distributed/` — Docker, PostgreSQL, Redis, Celery, leases, and recovery.
- `capabilities/` — capability catalog and provider map.
- `reference/` — package and command reference.

## Engineering records

- `adr/` — decisions that change architectural guarantees.
- `PRs/` — implementation-phase records.
- `implementation/` — technical implementation notes where useful.

Engineering records are not intended to replace the educational documentation.

## Current distributed stack

```text
Core
 │
 ├── Scheduler
 ├── Planner
 └── Executor
      │
      ▼
PostgreSQL WorkerBackend
      │
      ▼
Celery
      │
      ▼
Redis
      │
      ▼
Generic Worker
      │
      ▼
Capability Provider
```

The worker stack is deliberately capability-agnostic. For example, a Scrapy
crawler is a Crawl provider; it is not a special type of Celery worker.
