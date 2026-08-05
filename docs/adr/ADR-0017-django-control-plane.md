# ADR 0017 — Django control plane

## Status
Accepted

## Context
Mirror needs a control plane for auth, admin, and user-visible operations.

## Decision
Django SHALL be the control plane. Mirror Core MUST NOT depend on Django, but
Mirror applications MAY consume Mirror metadata through Django models.

## Consequences
Admin, auth, and dashboards can be built with Django instead of custom web code.
