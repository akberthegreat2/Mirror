# Signal Contract

Signals announce facts about runtime progress. They are for observability, not control flow.

## Core rules

- Signals may observe but should not change execution semantics.
- Signal handlers should be side-effect safe.
- Signal failures should be treated as observability failures, not as a reason to rewrite the pipeline outcome.

## Current core signal names

These names are emitted by the current runtime:

- `application.started`
- `application.shutting_down`
- `application.shutdown`
- `pipeline.started`
- `pipeline.finished`
- `pipeline.failed`
- `step.started`
- `step.succeeded`
- `step.failed`
- `step.skipped`
- `step.retrying`

## Current scope

The repository snapshot does **not** currently ship capability-specific signal modules such as `crawl.started` or `archive.started`. Capability-level signal families remain a future extension and should be added through an ADR before they become part of the public contract.

The snapshot also does **not** include automatic tests that keep capability-level signal names synchronized with this document. If those signal families are added later, the first commit that introduces them should also add matching contract tests.

## Receiver guidance

Receivers may log, measure, or export telemetry.
Receivers should not be the only place where a runtime guarantee exists.

## Event payloads

Payloads should be typed, stable, and documented alongside the signal names they belong to.
