# ADR 0018 — Celery and Redis workers

## Status
Accepted

## Context
Production execution needs a queueing and coordination layer.

## Decision
Celery SHALL be the official production task runner and Redis SHALL be the
official cache and queue coordination layer.

## Consequences
Production workers can scale without Mirror building its own queue system.
