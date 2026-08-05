# Project layout

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror needs a predictable scaffold so contributors and users know where to
put code, settings, tests, and docs.

## Decision

`mirror startproject` SHALL create the project shell. `mirror startapp` SHALL
create a reusable app package inside `apps/`. The scaffold MUST include a
project-local `manage.py`, a `config/` directory, an `apps/` directory, a
`tests/` directory, and a `docs/` directory.

## Consequences

The layout stays familiar to Django users and simple for new contributors.
