# Mirror Architecture Specification

**Version:** 1.2
**Status:** Approved
**Date:** 2026-08-07

This document is the constitutional contract for Mirror. It is normative. If code, tests, or other documentation disagree with this file, the code or the other document must change, or the feature must be marked experimental.

## 1. Scope

This document defines ownership, boundaries, dependency rules, and change control for Mirror.

It does not describe every package in the repository.
It does not serve as a roadmap.
It does not act as a tutorial.
It does not enumerate every current or future capability family.

Detailed package catalogs, examples, and future capability lists belong in reference docs, ecosystem docs, ADRs, and roadmaps.

## 2. Normative language

The words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are used as requirements in the RFC sense.

## 3. Architecture principles

Mirror is a capability kernel.

The kernel MUST remain capability-agnostic.
The kernel MUST own orchestration, execution, lifecycle, discovery, scheduling, signals, registries, storage abstractions, and middleware semantics.
Capabilities MUST own domain contracts only.
Providers MUST implement capability contracts only.
Services and workflows MAY compose multiple capabilities through published contracts.
Interfaces MAY expose the kernel through CLI, API, admin, or dashboard surfaces, but they MUST NOT bypass the kernel.

Mirror is open-source-first.
Core MUST NOT depend on proprietary vendor services.
Vendor-specific providers MAY exist as optional external plugins, but they MUST remain replaceable and non-essential.

## 4. Ownership rules

### Core

Core owns:
- execution
- planning
- compilation
- lifecycle
- discovery
- extension registration
- settings precedence
- registries
- middleware semantics
- signal dispatch
- worker abstraction
- scheduler abstraction
- metadata abstraction
- storage abstraction
- execution state

### Capability packages

A capability package owns:
- one domain contract;
- its request/result models;
- its error taxonomy;
- its typed protocol;
- its manifest metadata;
- its runner adapter, if needed.

A capability package MUST NOT:
- own framework infrastructure;
- own execution semantics;
- own discovery logic;
- own scheduling logic;
- own registry logic;
- own middleware semantics;
- own signal dispatch logic;
- instantiate unrelated providers.

### Provider packages

A provider package owns:
- one concrete implementation of a capability contract;
- its backend-specific configuration;
- backend-specific translation logic.

A provider package MUST NOT:
- create its own framework runtime;
- own orchestration;
- select unrelated providers;
- register itself outside the published extension mechanism;
- import another provider as a hidden implementation detail.

### Services and workflows

A service or workflow package MAY orchestrate capabilities.
It MUST do so through published contracts and core-owned orchestration.
It MUST NOT become a second framework.

### Interfaces

Interfaces such as CLI, API, admin, dashboards, or SDKs MAY expose Mirror functionality.
They MUST remain thin entry layers.
They MUST NOT replace or duplicate core orchestration.

## 5. Dependency rules

The dependency direction is strict:

- Core MUST NOT import capability or provider implementation packages.
- Capability packages MAY import Core and their own direct contract dependencies.
- Provider packages MAY import Core and the capability contract they implement.
- Capability packages MUST NOT import provider packages.
- Provider packages MUST NOT import other provider packages.
- Interface packages MUST NOT depend on private implementation details.
- Cross-capability collaboration MUST occur through public contracts, not through direct package coupling.

Cycles are prohibited.

## 6. Runtime responsibilities

Core is the only authority for:
- compiled plans;
- execution runs;
- runtime context;
- retry, timeout, and cancellation policy;
- middleware invocation;
- signal emission;
- worker leasing;
- scheduling decisions;
- metadata persistence;
- resource envelopes and lineage.

Capabilities and providers may observe those runtime facts, but they MUST NOT redefine them.

## 7. Extension model

Mirror uses a published extension model.
Extensions are discovered, validated, activated, deactivated, and unloaded according to core-owned rules.

Any transition from one extension API to another MUST preserve compatibility until a documented deprecation path exists.

Legacy compatibility layers MAY exist, but they MUST be treated as transitional and must not override the canonical extension model.

## 8. Prohibited patterns

The following patterns are prohibited:

- a capability package implementing its own executor or planner;
- a provider package implementing a second runtime;
- a package creating a hidden plugin registry;
- a capability package hardcoding provider selection;
- a package bypassing published contracts for convenience;
- a package importing proprietary vendor services as required dependencies of Core;
- a package reintroducing framework infrastructure after it has been centralized in Core.

## 9. Change control

Architectural changes require an ADR.

A change that affects ownership, dependency direction, runtime guarantees, or extension rules MUST be documented before it lands.

## 10. Documentation rule

This document is intentionally general.

Examples, current package inventories, future capability catalogs, and implementation-specific notes MUST live elsewhere.
