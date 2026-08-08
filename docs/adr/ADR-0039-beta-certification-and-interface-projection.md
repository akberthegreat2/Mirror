# ADR-0039 — Beta certification and interface projection

## Status

Accepted

## Context

Mirror now has multiple capability/provider packages and multiple interfaces.
A release can appear healthy while an entry point points at a missing module,
a manifest is malformed, or an interface duplicates discovery logic. Static
checks also need to cover the whole monorepo rather than only Core.

## Decision

Mirror will maintain a beta certification gauntlet with two related rules:

1. Every shipped capability and provider publishes its canonical manifest
   through the Core extension mechanism. Shipped interfaces publish
   `InterfaceManifest` objects through the same mechanism.
2. Interface packages consume an interface-neutral projection from
   `mirror_core.interfaces.InterfaceCatalog` rather than implementing their own
   manifest discovery protocol.

The projection layer is deliberately read-only and presentation-neutral. It
contains no Django, DRF, Typer, HTTP, HTML, Celery, Redis, or provider logic.

The certification suite must fail when an entry point references a missing
module or a manifest of the wrong kind. Optional external provider dependencies
may be absent from an offline environment, but that absence must be explicit
and those providers must be exercised in an integration environment before a
release is certified.

## Consequences

- CLI, Django, and REST can converge on the same catalog contract.
- Adding a capability requires a manifest and an entry point, not interface-
  specific registration code.
- Broken package metadata is caught before handover.
- External infrastructure remains a real integration gate rather than a fake
  in-process substitute.
