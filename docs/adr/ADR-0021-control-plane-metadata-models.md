# ADR 0021 — Control-plane metadata models

## Status
Accepted

## Context
The Django control plane needs a stable list of metadata objects to manage:
projects, pipelines, runs, steps, workers, schedules, crawled URLs, archives,
and checkpoints.

## Decision
Represent the control plane first as a pure-Python manifest with named model
specifications. The manifest will be the source of truth for later Django model
classes.

## Consequences
- Documentation can stay precise while Django remains optional in this
  workspace.
- Model names remain stable across the control plane and the docs.
- The package can be tested without importing Django.
