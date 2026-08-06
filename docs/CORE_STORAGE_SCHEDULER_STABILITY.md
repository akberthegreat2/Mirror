# Core storage and scheduler stabilization

This note records the cleanup that moved the local persistence backends out
of the old beta staging area and into stable core modules.

## What changed

- `mirror_core.storage` now defines the stable storage contracts:
  `MetadataRecord`, `MetadataStore`, and `BlobStore`.
- `mirror_core.storage` also provides the supported backends:
  `InMemoryMetadataStore`, `InMemoryBlobStore`, `SQLiteMetadataStore`, and
  `FileSystemBlobStore`.
- `mirror_core.scheduler` now presents the stable scheduling contract and
  backends: `ScheduleRecord`, `ScheduleState`, `SchedulerBackend`,
  `InMemoryScheduler`, and `SQLiteScheduler`.
- The old beta import path was removed, and the storage and scheduler tests
  now exercise the stable modules directly.

## Behavior fixes

- Metadata timestamps are now parsed back into `datetime` objects when data
  is loaded from SQLite.
- The filesystem blob store now rejects absolute paths and traversal
  segments instead of silently normalizing them.
- In-memory and SQLite schedulers now order due jobs and listings
  deterministically by due time, name, and schedule ID.
- The top-level `mirror_core` package re-exports the storage and scheduler
  contracts and backends for easier discovery.

## Validation

The updated tests cover the stable import paths and round-trip persistence
for the SQLite and filesystem backends.
