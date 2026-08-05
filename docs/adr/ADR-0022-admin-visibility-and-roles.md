# ADR 0022 — Admin visibility and roles

## Status
Accepted

## Context
Operators, technicians, and viewers need different levels of access to Mirror
metadata and worker controls.

## Decision
Define admin visibility and role boundaries in the control-plane docs before
implementing the actual Django admin classes.

## Consequences
- Role names become part of the project vocabulary.
- Admin pages can be added later without renegotiating ownership.
- The control plane can document operator workflows separately from execution
  contracts.
