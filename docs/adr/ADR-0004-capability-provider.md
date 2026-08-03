# ADR-0004: Separation of Capability and Provider

## Status
Accepted

## Context
In many frameworks, the interface and implementation are coupled (e.g., a `Fetcher` class that does everything). This makes it hard to swap implementations (HTTPX vs Playwright) and hard to evolve the capability contract independently.

## Decision
We separate the **capability** (the contract, models, signals, and runner) from the **provider** (the concrete implementation). A capability owns the definition; a provider implements the protocol. Capability never imports provider. Providers declare which capability API version they support.

## Consequences
- Multiple providers can implement the same capability.
- Capability evolution is separate from provider updates.
- A provider can be installed without altering the capability package.
- The planner can resolve providers based on settings or step-level overrides.
- Testing is simplified (contract tests live in the capability package).

## Alternatives Considered
- **Single class**: Coupled; hard to swap.
- **Abstract base class in capability**: Still imports provider implementations? No, that would be fine, but the separation is stronger with descriptors.
- **No versioning**: Would break compatibility; we enforce version constraints.

## Decision Rationale
Separation enables the pluggability Mirror is built on. It makes the framework extensible without modifying core or capabilities.
