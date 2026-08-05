# Signals

Signals announce facts about runtime progress. They are for observability,
not control flow.

## Core bus

`mirror_core.signals.SignalBus` provides named signal registration and
emission for both sync and async receivers.

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

## Guidance

Receivers should be side-effect safe. Signal failures should be treated as
observability problems, not a reason to change pipeline semantics.
