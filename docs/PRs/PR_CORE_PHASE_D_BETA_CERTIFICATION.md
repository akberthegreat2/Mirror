# PR: Phase D beta certification and final hardening

## Problem

The runtime and control plane had reached the point where package metadata,
Django lifecycle, static typing, and interface discovery could drift even while
individual unit tests remained green.

## Decision

Use Phase D to harden the current patched tree rather than introduce another
runtime. The phase adds a shared interface-neutral manifest projection,
repository-wide typing/lint gates, capability/provider/interface manifest
certification, Django migrations, immutable pipeline-version behavior, and
release-oriented documentation.

## What changed

- Added `mirror_core.interfaces.InterfaceCatalog`.
- Added CLI manifest inspection commands.
- Added `InterfaceManifest` entry points for the Django dashboard and REST API.
- Added certification tests for all shipped capability and provider entry
  points.
- Fixed broken provider entry points discovered by certification.
- Added the first Django migration for the control-plane package.
- Made managed pipeline versions immutable at the admin/API surface.
- Added explicit code-defined/read-only versus managed/editable documentation.
- Fixed all repository ruff violations and repository mypy violations under the
  declared integration-boundary policy.
- Added beta certification and pipeline reference documentation.

## Validation

The final validation record is kept in `HANDOVER.md` and must include the full
pytest result, ruff result, mypy result, and any explicitly skipped external
lab tests.
