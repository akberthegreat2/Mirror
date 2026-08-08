# mirror-control-django

`mirror-control-django` is Mirror's reusable Django control-plane app. It keeps
Mirror Core free of Django while giving operators a Django admin surface for
projects, pipelines, versions, executions, workers, schedules, crawled URLs,
archives, checkpoints, and dead letters.

## What it provides

- a pure-Python control-plane manifest that describes the admin surface;
- Django models for the control-plane objects;
- Django admin registrations;
- a blob-backed pipeline repository for managed pipeline definitions;
- a lightweight dashboard view that summarizes the control plane.

## How it fits Mirror

Mirror Core owns execution semantics. This package owns the human-facing
control plane. Pipelines are stored as versioned blob documents; the database
stores metadata and indexes.
