# ADR 0006 — Worker contract

## Status
Accepted

## Context
Mirror needs a standard worker shape before distributed backends arrive.

## Decision
Mirror Core SHALL define worker contracts. Implementations MAY be local,
SQLite-backed, Celery-backed, or future backends.

## Consequences
Worker behavior is standardized before cluster execution is added.
