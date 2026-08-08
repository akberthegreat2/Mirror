# mirror-core

`mirror-core` is Mirror's framework kernel.

It is intentionally **capability-agnostic**. Core knows how to discover,
validate, compile, schedule, execute, and observe work. It does not know how to
crawl a website, call HTTPX, parse a WARC, search a database, or run an AI model.
Those behaviors belong to capability/provider packages.

## Install

```bash
pip install mirror-core
```

## Core flow

```text
Pipeline
  ↓
PipelineCompiler
  ↓
ExecutionPlan
  ↓
Executor
  ↓
Capability + Provider
  ↓
ResourceEnvelope
```

For local work, use `InlineWorker` or `SQLiteWorkerBackend`. For distributed
work, install `mirror-worker-postgres` and `mirror-execution-celery`.

## What Core owns

- extension discovery and validation;
- settings and lifecycle;
- pipeline planning and compilation;
- execution state and runtime contexts;
- retry, timeout, fallback, and cancellation semantics;
- middleware and signals;
- scheduling and worker contracts;
- metadata, checkpoint, artifact, and dead-letter contracts.

## What Core does not own

Core does not import concrete providers. A provider package implements one
capability contract and is discovered through the published extension API.

That boundary is tested by the architecture test suite and is mandatory for
future work.

## Documentation

The educational Core guide is in `docs/concepts/core.md`. The constitutional
rules are in `docs/ARCHITECTURE.md`.
