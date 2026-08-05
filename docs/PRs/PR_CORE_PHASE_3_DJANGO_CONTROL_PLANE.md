# PR: Phase three Django control plane

## Problem

Mirror needs a real operator surface. The framework can already execute work,
but users still need a place to inspect runs, crawled URLs, archives, workers,
and schedules.

## Decision

Add a Django control-plane package that owns the metadata manifest and the
future admin-facing model boundary.

## What changed

- Added a control-plane manifest package for Django projects.
- Added Django settings fragment rendering for the Mirror control plane.
- Added tests for the manifest and the Django-availability guard.
- Added docs, ADRs, and tutorial/reference pages for the control plane.

## Validation

- The control-plane manifest tests pass without Django installed.
- The generated Django settings fragment is copy-paste friendly.

## Deferred

- real Django model classes and admin registrations;
- auth/roles wiring;
- control-plane UI pages;
- Django integration tests once Django is available in the environment.
