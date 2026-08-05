# ADR 0014 — Scheduler contract

## Status
Accepted

## Context
Recurring work must be a first-class concept.

## Decision
Scheduling SHALL be implemented as a backend contract that submits future work,
pause jobs, and resume jobs. It MUST NOT own business logic.

## Consequences
Recurring jobs become observable and replaceable.
