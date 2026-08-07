# PR: extension migration audit

## Summary

This phase documents the audit required to move shipped packages onto the canonical core extension model without breaking compatibility.

## Why this exists

The repository still contains legacy registry vocabulary alongside the canonical manifest extension path.

That is acceptable while migration is in progress, but it must be visible in the repo so contributors know which path is canonical and which path is transitional.

## What this phase records

- the current legacy registry usage in shipped packages;
- the canonical extension model in `mirror_core.extensions`;
- the compatibility shim boundary, if any;
- the list of packages that still need migration work;
- the beta gate for final convergence.

## What is deferred

- removal of compatibility shims before the migration plan is complete;
- any provider or capability redesign that is not required for the transition;
- proprietary provider discussions, which belong in the ecosystem catalog and the open-source-first policy ADR.
