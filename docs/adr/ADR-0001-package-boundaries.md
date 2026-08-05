# ADR 0001 — Package boundaries

## Status
Accepted

## Context
Mirror Core must never become a hidden dependency sink for capability code.

## Decision
Mirror Core SHALL remain capability-agnostic. Capabilities MAY depend on core.
Providers MAY depend on their capability and core. Core MUST NOT import capability,
provider, or interface packages.

## Consequences
Package boundaries become a testable part of the public contract.
