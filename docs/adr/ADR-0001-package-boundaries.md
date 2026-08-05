# Package boundaries

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror Core must stay capability-agnostic. The framework already has separate
packages for core, capabilities, providers, middleware, CLI, and contract
testing. The repo must not return to a monolithic layout.

## Decision

Mirror Core SHALL NOT import capability or provider packages. Capability
packages MAY depend on Mirror Core. Provider packages MAY depend on their
capability package and Mirror Core. Interfaces MAY depend on Mirror Core and, if
needed, on capability metadata.

## Consequences

This keeps the runtime modular and prevents the core from becoming a hidden
application framework for one domain.
