# ADR-0028 — Extension model and plugin lifecycle

## Status

Accepted

## Context

Mirror is designed as an ecosystem of installable packages, not a single monolithic application. The architecture already distinguishes between capabilities, providers, middleware, interfaces, storage backends, workers, and schedulers. That separation needs a single, explicit extension model so the framework does not drift back toward hardcoded integrations.

This proposal is about ownership and lifecycle, not about adding more framework layers.

## Decision

Mirror Core SHOULD own the extension model for all package families that participate in runtime discovery.

The canonical extension families are expected to include:

- capabilities;
- providers;
- middleware;
- interfaces;
- storage backends;
- worker backends;
- scheduler backends;
- signal families;
- future knowledge-infrastructure plugins.

The extension model SHOULD follow these rules:

- discovery is entry-point based or otherwise explicitly registered through Core;
- installed does not mean activated; settings decide activation;
- each extension family has a descriptor or manifest that declares its contract, version, settings schema, dependencies, and health-check surface where relevant;
- capability packages define contracts and tests;
- provider packages implement those contracts;
- interface packages expose CLI, admin, API, or SDK surfaces;
- first-party packages obey the same rules as third-party packages;
- no package family gets privileged access to Core ownership rules.

The plugin lifecycle SHOULD be explicit:

1. discover;
2. validate;
3. configure;
4. activate;
5. run;
6. deactivate;
7. unload.

Core SHOULD remain the only place where extension lifecycle semantics are defined.

The current implementation scope in this repository covers capability, provider, middleware, interface, and storage manifests plus explicit lifecycle records. Worker, scheduler, and signal extension families remain future extension families rather than shipped manifest types.

## Consequences

- third-party extensions can be added without patching Core;
- lifecycle records remain immutable snapshots of the manifest state that Core observed;
- the repository can prove its own extension model through first-party packages;
- package boundaries remain testable;
- the architecture can later absorb AI/knowledge plugins without changing the kernel.

## Non-goals

- hardcoding provider selection inside capability packages;
- creating a separate plugin registry outside Core;
- making one package family privileged over another;
- turning extension lifecycle into application-specific business logic.
