# Mirror Architecture Specification

**Version:** 1.0  
**Status:** Approved  
**Date:** 2026-08-03

> This document is a contributor contract.
> It is not a product overview and it is not user documentation.

---

## 1. Scope

Mirror is an application framework for building web infrastructure.

Mirror Core is the stable kernel. It does not know about one particular crawler,
one particular archive format, or one particular dashboard.

All domain behavior lives in capabilities, providers, middleware, workers,
interfaces, and storage adapters.

---

## 2. Normative terms

The words **MUST**, **MUST NOT**, **SHALL**, **SHOULD**, and **MAY** are used
with their normal RFC meaning.

If this document says a component MUST do something, the code, tests, and docs
MUST all agree.

---

## 3. Non-negotiable principles

| Principle | Meaning |
|---|---|
| Core knows nothing | `mirror_core` MUST remain capability-agnostic. It MUST NOT import capability or provider packages. |
| Discovery, not hardcoding | Extensions MUST be discovered through entry points. No hardcoded package lists. |
| Installed ≠ activated | Installing a package does not make it active. Settings choose the active components. |
| Typed boundaries | Data between components MUST use typed models. |
| Capability owns provider | A capability defines the contract; a provider implements it. |
| DAG, not list | Pipelines MUST compile to directed acyclic graphs. |
| Deterministic configuration | Settings precedence MUST be fixed and documented. |
| Transactional lifecycle | Startup MUST roll back on failure. Shutdown MUST reverse initialization. |
| Observability first | Signals, middleware, and logging are core features, not optional extras. |

---

## 4. Package topology

Current repository packages:

```
packages/
├── mirror_core/
├── mirror_fetch/
├── mirror_fetch_httpx/
├── mirror_fetch_playwright/
├── mirror_archive/
├── mirror_archive_warc/
├── mirror_middleware/
├── mirror_cli/
└── mirror_testing/
```

### Dependency rules

- capability → `mirror_core`
- provider → capability
- provider → `mirror_core`
- interface → `mirror_core`
- interface → capability only when it needs runtime discovery support

**No cycles are allowed.**

---

## 5. Core subsystems

| Subsystem | Responsibility |
|---|---|
| Application | Composition root. Owns registry, settings, signals, middleware, and the execution engine. |
| Registry | Holds discovered descriptors. |
| Discovery | Loads entry points and classifies descriptors. |
| Settings | Resolves defaults, file, environment, and runtime overrides. |
| Lifecycle | Starts and stops components in a transactional order. |
| Signals | Announces events for observability. |
| Middleware | Wraps execution and can observe or modify it. |
| Pipeline | Declares the work as a DAG. |
| Planner | Compiles and validates the DAG into an execution plan. |
| Executor | Runs a compiled plan. |
| Resources | Tracks typed outputs with provenance. |
| Workers | Owns job execution, leases, checkpoints, and completion rules. |
| Exceptions | Defines framework-specific failure types. |

---

## 6. Required invariants

Mirror Core MUST satisfy all of the following:

1. Capability packages MUST NOT import provider packages.
2. Providers MUST NOT depend on the application runtime outside their contract.
3. Pipelines MUST be compiled before execution.
4. Execution MUST run a compiled plan, not raw discovery results.
5. Each execution run MUST own its own mutable state.
6. Middleware MUST be explicitly ordered.
7. Signals MUST NOT control business logic.
8. Worker contracts MUST exist before distributed workers are added.
9. Resource envelopes MUST preserve provenance.
10. New architecture decisions MUST be recorded in ADRs.

---

## 7. Configuration

Settings precedence is:

1. defaults
2. configuration file
3. environment variables
4. runtime overrides

Secrets MUST be redacted in dumps and reprs.

Settings MUST be frozen after validation.

---

## 8. Scope of alpha

Alpha includes:

- project scaffolding;
- local worker contracts;
- middleware contracts;
- signals;
- fetch and archive packages;
- CLI discovery and scaffold commands;
- install-and-run smoke tests;
- contract tests.

Alpha does not include:

- distributed workers;
- dashboard and Django integration;
- REST or GraphQL APIs;
- cluster scheduling;
- SaaS tenancy;
- billing;
- custom database engines;
- custom object storage engines.

Those belong in later phases and ADRs.

---

## 9. Review rule

If a behavior is promised, it MUST appear in:

1. code,
2. tests,
3. docs.

If one of those is missing, the promise is incomplete.
