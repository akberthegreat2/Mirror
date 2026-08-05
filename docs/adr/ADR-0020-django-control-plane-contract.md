# ADR 0020 — Django control-plane contract

## Status
Accepted

## Context
Mirror needs a human-facing control plane for metadata, admin operations, and
operator workflows. That surface must not leak Django into Mirror Core.

## Decision
Create a dedicated Django control-plane package that describes the metadata
contract, admin boundary, and settings fragment needed by a Django project.

## Consequences
- Mirror Core stays Django-free.
- The repository can document and test the control-plane contract without
  requiring Django at import time.
- Django model classes and admin registrations can be added later without
  changing the execution engine.
