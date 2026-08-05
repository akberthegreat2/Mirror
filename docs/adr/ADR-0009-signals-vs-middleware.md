# Signals vs middleware

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror uses both signals and middleware. They are not the same thing.

## Decision

Signals MUST announce events only. Middleware MAY control flow. Signal
handlers MUST NOT alter pipeline semantics. Middleware MUST be the place where
execution changes happen.

## Consequences

The code stays easier to debug because observation and control have separate
homes.
