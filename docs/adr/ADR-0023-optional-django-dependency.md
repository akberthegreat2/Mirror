# ADR 0023 — Optional Django dependency

## Status
Accepted

## Context
The workspace must remain installable and testable even when Django is not
available in the environment.

## Decision
Keep Django as an optional dependency for the control-plane package. Pure-Python
helpers and docs may exist without Django, while Django integrations can be
enabled in projects that install it.

## Consequences
- The repository can validate control-plane contracts in environments without
  Django.
- Django-specific integration work remains explicit and optional.
- Missing-Django environments get a clear error message instead of an import
  crash.
