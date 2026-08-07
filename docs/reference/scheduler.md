# Scheduler reference

A scheduler decides when jobs should run.

Mirror now exposes scheduling as a core contract plus a core-owned coordinator. The scheduler can:

- queue a job for later;
- pause a job;
- resume a job;
- hand work to workers;
- record schedule state through the metadata store.

## Core types

- `ScheduleTrigger`
- `ScheduleRecord`
- `SchedulerBackend`
- `SchedulerCoordinator`
- `SQLiteScheduler`
- `InMemoryScheduler`
