# PR: Remove the parallel framework layer

This change removes the old parallel package and keeps Mirror focused on
one framework: `mirror_core`.

## Why

Mirror should not have two execution systems, two signal buses, two middleware
chains, or two plugin registries.

The parallel package had started to act like a second framework. That made the
architecture harder to reason about and easier to drift.

## What changed

- deleted the `mirror_parallel framework` package;
- removed parallel-layer-specific docs and scorecards;
- replaced the old parallel framework references with a capability-package overview;
- kept capability packages separate and focused on their own domain contracts.

## What stays

- `mirror_core` stays the single framework kernel;
- capability packages stay small and replaceable;
- provider packages stay responsible for implementation;
- services and workflows can compose multiple capabilities through public
  contracts only.
