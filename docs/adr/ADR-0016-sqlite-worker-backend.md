# ADR-0016: SQLite worker backend

Status: Accepted

## Decision

Mirror ships a SQLite-backed worker backend for single-machine beta setups.

## Reason

SQLite is good enough for development, demos, and small deployments. It gives
contributors a real persistence path without requiring Redis or Celery on day
one.
