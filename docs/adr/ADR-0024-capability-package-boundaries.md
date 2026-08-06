# ADR-0024: Capability package boundaries

## Status

Accepted

## Context

Mirror must avoid a second framework hidden inside a capability bundle. The
core runtime already owns planning, execution, lifecycle, discovery, middleware,
signals, storage, scheduling, and workers.

Capability packages should therefore stay focused on their own domain concepts
and public contracts.

## Decision

Keep the repository split into three layers:

1. `mirror_core` for framework infrastructure;
2. capability packages for domain contracts and models;
3. provider packages for concrete implementations.

Do not add a parallel web-infra framework package.

## Consequences

- contributors have one place to look for framework behavior;
- capabilities stay replaceable;
- providers stay interchangeable;
- workflows can compose capabilities without importing private internals;
- the repository avoids duplicated runtimes, duplicated middleware, and
  duplicated registries.
