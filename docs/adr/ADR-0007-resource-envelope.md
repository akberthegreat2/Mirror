# ADR 0007 — Resource envelope

## Status
Accepted

## Context
Resources must preserve provenance and remain stable across execution phases.

## Decision
Resource envelopes SHALL be immutable and SHALL carry payload, provenance,
type, schema version, and fingerprint information.

## Consequences
Lineage is stable and later distributed serialization is easier to add.
