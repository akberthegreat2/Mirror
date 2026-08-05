# ADR 0016 — SQLite worker backend

## Status
Accepted

## Context
Contributors need a zero-dependency worker backend for development and CI.

## Decision
SQLite SHALL be the official local-development worker backend.

## Consequences
Worker semantics can be verified without Redis or Celery.
