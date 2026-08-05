# Signal Contract

Signals announce facts about runtime progress. They are for observability, not control flow.

## Core rules

- Signals may observe but should not change execution semantics.
- Signal handlers should be side-effect safe.
- Signal failures should be treated as observability failures, not as a reason to rewrite the pipeline outcome.

## Common signal names

- `application.started`
- `application.shutting_down`
- `application.shutdown`
- `pipeline.started`
- `pipeline.finished`
- `step.started`
- `step.succeeded`
- `step.failed`
- `step.skipped`
- `worker.started`
- `worker.stopped`
- `worker.heartbeat`
- `resource.created`

## Receiver guidance

Receivers may log, measure, or export telemetry.
Receivers should not be the only place where a runtime guarantee exists.

## Event payloads

Payloads should be typed, stable, and documented alongside the signal names they belong to.


## Rule

Signals observe the system. Signals MUST NOT change execution flow. Middleware
controls flow; signals report what happened.
