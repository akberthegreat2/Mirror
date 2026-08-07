# PR: Phase five extension unification

## Problem

Mirror now has a newer extension system in Core, but the repository still has to make the canonical path unmistakable for contributors and package authors.

## Decision

Make the Core extension model the primary story in the docs and package references while preserving compatibility where needed.

## What changed

- clarified the extension-system narrative in the docs;
- documented the canonical extension path in the architecture notes;
- kept the compatibility story explicit instead of implicit;
- aligned future ADRs with the Core-owned extension model.

## Validation

- architecture docs and ADR index point to the same extension story;
- the package layout remains capability-first and provider-first;
- compatibility is documented rather than hidden.

## Deferred

- removing any remaining compatibility aliases only after the migration story is complete;
- third-party ecosystem packaging conventions.
