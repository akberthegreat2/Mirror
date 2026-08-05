# ADR 0009 — Signals vs middleware

## Status
Accepted

## Context
Signals and middleware are both cross-cutting concerns, but they serve different
purposes.

## Decision
Signals SHALL observe. Middleware SHALL control. Signals MUST NOT alter execution
flow.

## Consequences
Observers remain side-effect safe and predictable.
