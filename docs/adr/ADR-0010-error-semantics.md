# ADR 0010 — Error semantics

## Status
Accepted

## Context
Terminal outcomes must mean different things, not just different labels.

## Decision
abort fails the pipeline, continue records a failure and allows later work, and
skip marks the step as skipped without counting as a failure.

## Consequences
Terminal outcomes stay meaningful and testable.
