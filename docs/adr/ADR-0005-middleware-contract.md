# ADR 0005 — Middleware contract

## Status
Accepted

## Context
Middleware is part of the runtime contract, not an implementation detail.

## Decision
Middleware SHALL be constructed through the same descriptor/settings path as
providers. Middleware MAY continue, short-circuit, retry, or transform
invocation state.

## Consequences
Middleware behavior becomes testable, documented, and discoverable.
