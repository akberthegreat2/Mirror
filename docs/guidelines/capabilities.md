# Capability package guidelines

Use these rules when changing any Mirror capability package.

## Keep the package small

A capability package should usually contain:

- public models;
- a protocol or contract;
- errors;
- a descriptor;
- optional signal names;
- optional helper types that describe the domain.

## Do not put framework code here

Do not add:

- a second executor;
- a second planner;
- a second middleware system;
- a second registry;
- lifecycle management;
- global discovery;
- provider selection logic;
- workflow orchestration.

Those belong in `mirror_core` or in a service layer.

## Keep dependencies narrow

A capability package should depend on:

- `mirror_core`;
- the standard library;
- and only the smallest supporting libraries needed to describe the contract.

Provider-specific dependencies belong in provider packages.

## Prefer explicit exports

Use explicit imports and explicit `__all__` declarations. That keeps the
package easy to read and easy to replace.
