# ADR-0041: Core Test Isolation and Safe Metadata Decoding

## Status

Accepted

## Context

`mirror_core` is the framework kernel and must be independently testable.
Repository architecture checks and capability integration tests intentionally
need the wider monorepo, but they must not be hidden inside the Core package
test suite.

Core metadata also persists type information for values such as enums.
Persisted metadata is not a trusted Python import instruction. Automatically
importing a module named by stored data would make decoding capable of executing
arbitrary module initialization.

## Decision

1. Core-owned unit and contract tests remain under `packages/mirror_core/tests`.
2. Repository-wide architecture and capability integration tests live under the
   root `tests/` tree.
3. Enum metadata rehydration never imports an arbitrary module from persisted
   data. It resolves explicitly registered enum types first, then types from
   modules already loaded by the trusted application. Unknown enum references
   degrade to their stored value.
4. Applications that require enum identity after a fresh process starts must
   call `register_metadata_enum()` during trusted initialization.

## Consequences

Core can be installed and tested without capability packages. The repository
still retains its stronger monorepo architecture and integration certification
suite. Metadata decoding is safe against import-triggering persisted payloads,
while explicit registration preserves deterministic cross-process enum
rehydration.
