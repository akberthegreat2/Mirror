# PR: Phase three developer experience

## Problem

The repository could prove the runtime in tests, but it did not yet give a new contributor a standard project/app layout or a quick way to verify a fresh scaffold.

## Decision

Add a Django-style developer experience layer to the CLI:

- `mirror startproject`
- `mirror startapp`
- `mirror doctor`

## What changed

- Added scaffold generation helpers.
- Added project and app templates.
- Added doctor health checks.
- Added CLI tests for the new commands.
- Added developer-experience docs and a CLI reference.
- Documented the repo-local `conftest.py` and `sitecustomize.py` bootstrap files.

## Validation

- CLI tests cover project scaffolding, app scaffolding, and doctor checks.
- The full package test suite remains green.

## Deferred

- dashboard / Django integration;
- distributed workers;
- beta-only SaaS services.
