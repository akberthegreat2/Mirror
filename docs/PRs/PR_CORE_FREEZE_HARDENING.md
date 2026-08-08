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

## Final contract hardening

- Made `Step.on_error` semantics explicit: `abort` cancels the run,
  `continue` permits independent branches while leaving dependents unrunnable,
  `skip` marks transitive dependents skipped, and `fallback` records terminal
  failure only after configured fallback providers are exhausted.
- Added regression coverage for independent and dependent branches under both
  `continue` and `skip`.
- Documented that Core owns step retry/timeout policy while middleware retry and
  timeout are explicit, composable middleware behavior and must not be assumed
  to replace Core policy.
- Removed the unused `httpx` dependency from `mirror-scrape`.
- Corrected the stale middleware fallback contract sentence.


## Final freeze certification hardening

- Made in-memory dead-letter ordering newest-first, matching SQLite.
- Added direct enum metadata round-trip and nested-value coverage.
- Added explicit `register_metadata_enum()` support for safe cross-process enum
  rehydration without importing modules named by persisted data.
- Moved repository-wide architecture and capability integration tests out of the
  standalone Core package test suite.
- Updated the root test configuration and handover documentation to distinguish
  standalone Core certification from monorepo certification.
- Removed the unreachable fallback-exhaustion exception path.


## Certification result

The final candidate was tested with the supplied offline dependency wheels.
Core alone passes 119 tests; the complete repository passes 296 tests with five
explicit external-service tests skipped. Ruff reports no selected-rule
violations, and mypy reports no issues across 53 Core/CLI/worker/Celery source
files.
