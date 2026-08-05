# Signals

Signals are announcements about what just happened.

They are for observation, not for control.

## Common uses

- logging
- metrics
- tracing
- progress reporting
- audit trails

## Typical signal names

- `application.started`
- `pipeline.started`
- `step.started`
- `step.finished`
- `step.failed`
- `worker.started`
- `worker.stopped`

## Rule of thumb

If you want to change what the pipeline does, use middleware.
If you want to be told what happened, use signals.
