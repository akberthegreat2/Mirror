# ADR 0008 — Settings authority

## Status
Accepted

## Context
Configuration should be deterministic and safe to inspect.

## Decision
Settings SHALL follow this precedence: defaults -> file -> environment -> runtime.
Secrets MUST be redacted in dumps and MUST NOT leak into merge operations.

## Consequences
Project configuration is reproducible and safe to audit.
