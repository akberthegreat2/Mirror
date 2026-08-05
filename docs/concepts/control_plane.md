# Control plane

Mirror uses Django as the control plane.

The control plane is where people look at jobs, runs, workers, archives, and
crawled URLs. It is not where Mirror executes the work. Mirror Core runs the
pipelines; Django helps humans inspect and manage the results.

## Why this split exists

- Mirror Core stays small and stable.
- Django gives Mirror auth, admin, permissions, and forms.
- The control plane can grow without changing the execution engine.

## What belongs in the control plane

- project metadata;
- pipeline runs;
- workers;
- schedules;
- crawled URLs;
- archive records;
- checkpoints.

## What does not belong there

- pipeline execution logic;
- retry logic;
- middleware logic;
- provider logic;
- storage backends.
