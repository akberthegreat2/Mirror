# Discovery and entry points

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror loads extension metadata through Python entry points. Hardcoded plugin
lists would make the framework brittle and difficult to extend.

## Decision

All extension types MUST be discovered through entry points. The registry MUST
store immutable descriptor objects. Discovery MUST report duplicates and invalid
descriptors before runtime starts.

## Consequences

New capabilities and providers can be added without editing the core
application registry.
