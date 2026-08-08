# Connect Mirror to Django admin

Mirror's control plane is a reusable Django app. It exposes projects,
pipelines, versions, runs, steps, workers, schedules, crawled URLs, archives,
checkpoints, and dead letters without moving execution semantics into Django.

## What you get

- Django admin for operator workflows;
- a project-level dashboard page;
- blob-backed pipeline versions;
- read-only handling for code-defined pipelines;
- managed pipelines that can be edited and versioned;
- a manifest catalog that the CLI, dashboard, and REST API can all read.

## Typical setup

1. Install Django and `mirror-control-django`.
2. Add `mirror_control_django` to `INSTALLED_APPS`.
3. Point `MIRROR_CONTROL_BLOB_ROOT` at a writable document store path.
4. Run `python manage.py migrate`.
5. Add `path("mirror-control/", include("mirror_control_django.urls"))` to your URL configuration.
6. Open Django admin and the dashboard view.

## Pipeline lifecycle

- code-defined pipelines are registered as read-only records;
- the control plane stores a blob snapshot for inspection;
- the user can materialize a managed pipeline from that snapshot;
- managed pipelines can be edited and versioned;
- each version points at an immutable blob document.

## What Mirror still owns

Mirror Core owns the pipeline engine, scheduler, workers, retries, and
execution semantics. Django owns the human-facing control plane and the
metadata that describes those executions.
