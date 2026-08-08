# PR: Core freeze hardening

## Problem

Coverage review identified four freeze risks: the hand-written condition
sandbox had only indirect coverage, an orphaned duplicate import resolver was
still shipped, SQLite durability stores lacked direct tests, and lease
reclamation was exposed as a manual method without an automatic distributed
invoker.

## Changes

- Added direct condition-evaluator regression and adversarial security tests.
- Removed `mirror_core.extensions.resolve`, leaving `mirror_core.imports` as the
  single import-resolution implementation.
- Added direct SQLite checkpoint and dead-letter persistence tests, including
  reopen, JSON round-trip, upsert, ordering, and replay behavior.
- Made SQLite dead-letter listing newest-first.
- Added the Celery `mirror.requeue_expired` task and Beat schedule.
- Added the dedicated `mirror.reaper` queue to the generic worker command.
- Added a `mirror-celery-beat` entry point and Docker Compose Beat service.

## Validation

The freeze gate is: direct core tests, full repository tests, Ruff, mypy, and
manifest/import smoke tests must pass. External PostgreSQL/Redis integration
remains separately marked as integration testing when those services are not
available in the execution environment.
