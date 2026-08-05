# Settings authority

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror needs one clear settings story. Contributors and users should not have
to guess which value wins.

## Decision

Settings precedence MUST be defaults → file → environment → runtime.
Secrets MUST be redacted. Settings SHOULD be frozen after validation. Project
scaffolds MUST show the source of truth in one place.

## Consequences

The framework behaves predictably when it grows into a real SaaS control
plane.
