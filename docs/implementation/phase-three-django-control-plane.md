# Phase three: Django control plane

**Status:** Planned boundary; the package is not shipped in this snapshot.

## Goal

Give Mirror a Django-based control plane for metadata, users, admin pages, and
operator workflows without moving any of that responsibility into Mirror Core.

## Documented so far

- control-plane ADRs and docs that define the intended boundary;
- a Django settings-fragment contract;
- model and admin metadata specs for projects, runs, steps, workers,
  schedules, crawled URLs, archive records, and checkpoints.

## Still to do

- Django model classes and admin registrations;
- auth and roles;
- dashboard views for runs, crawled URLs, archives, and workers;
- optional Django app packaging;
- integration tests once Django is available in the environment.

## Non-goals

- Mirror Core MUST NOT import Django.
- Mirror Core MUST NOT depend on any control-plane models.
- The control plane MUST remain replaceable at the package boundary.
