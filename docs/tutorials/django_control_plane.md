# Connect Mirror to Django admin

Mirror keeps execution in the framework and metadata in the control plane.
This tutorial shows the contract the Django side should implement.

## What you get

- a control plane for projects, runs, workers, schedules, crawled URLs, and
  archives;
- Django admin as the operator UI;
- a settings fragment you can copy into a Django project.

## Start here

1. Install Django in the project that will host the control plane.
2. Copy the settings fragment from the Mirror control-plane package.
3. Register the Mirror metadata models in Django admin.
4. Use Django auth and permissions for operators and technicians.

## What Mirror still owns

Mirror Core owns the pipeline engine, workers, retries, and storage contracts.
Django owns the people-facing control plane.
