# Signal Contract

Signals announce facts about runtime progress. They are for observability, not control flow.

## Core rules

- Signals may observe but should not change execution semantics.
- Signal handlers should be side-effect safe.
- Signal failures should be treated as observability failures, not as a reason to rewrite the pipeline outcome.

## Common signal names

### Core (`mirror_core`)

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

### Capability-level signals

Capability packages define their own signal names, under the same rules as
core signals (observe only, typed payloads, non-critical by default). These
are just as stable a promise as the core list above — a name changing here
is a breaking change like any other.

`mirror_crawl` (`mirror_crawl.signals`):

- `crawl.started`
- `crawl.page.discovered`
- `crawl.page.stored`
- `crawl.finished`

`mirror_archive` (`mirror_archive.signals`):

- `archive.started`
- `archive.succeeded`
- `archive.failed`

A test in each capability package (`test_signal_contract_names_match_docs`)
asserts these string values match this file, so this section cannot drift
from the code silently.

## Receiver guidance

Receivers may log, measure, or export telemetry.
Receivers should not be the only place where a runtime guarantee exists.

## Event payloads

Payloads should be typed, stable, and documented alongside the signal names they belong to.


## Rule

Signals observe the system. Signals MUST NOT change execution flow. Middleware
controls flow; signals report what happened.
