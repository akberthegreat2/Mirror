# Error semantics

**Status:** Accepted  
**Date:** 2026-08-05

## Context

A pipeline needs clear terminal states. Contributors must be able to tell
the difference between a failure, a skipped step, and a partial success.

## Decision

The runtime SHALL treat abort, continue, and skip as distinct policies.
Abort fails the run. Continue records the failure but lets the run continue.
Skip marks the step as intentionally omitted. Fallback, if supported later,
MUST be compiled explicitly rather than implied.

## Consequences

Users get predictable outcomes and contributors get a contract they can test.
