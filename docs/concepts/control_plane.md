# Control plane

Mirror uses Django as the control plane. The control plane is the human-facing
surface that shows projects, pipelines, versions, runs, workers, schedules,
crawled URLs, archives, checkpoints, and dead letters. It does not execute
work itself. Mirror Core runs the pipeline engine; Django helps humans inspect
and manage the results.

## What the control plane manages

- project metadata;
- code-defined pipeline snapshots;
- managed pipeline versions;
- pipeline run history;
- per-step execution records;
- worker records and heartbeats;
- schedules and operational policies;
- crawled URLs and archive records;
- checkpoints and dead-letter records.

## Pipeline storage model

Pipeline definitions are materialized as blobs. The database stores metadata and
indexes, while the blob store stores the actual document. Code-defined pipelines
are read-only until a user explicitly materializes them into a managed
pipeline. Managed pipelines can then be edited and versioned.

## Why this split exists

- Mirror Core stays small and stable.
- Django gives Mirror auth, admin, permissions, and forms.
- The control plane can grow without changing the execution engine.
- REST consumers can reuse the same catalog and models without inventing a
  second control plane.

## What does not belong there

- pipeline execution logic;
- retry logic;
- middleware logic;
- provider logic;
- storage backends;
- worker leasing rules.

Those stay in Mirror Core and the worker backends.
