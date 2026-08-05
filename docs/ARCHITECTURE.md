# Mirror Architecture Specification

**Version:** 1.0
**Status:** Approved
**Date:** 2026-08-05

This document is a contributor contract. It states the rules that Mirror code,
tests, and docs must follow. If code and this document disagree, the code must
change or the feature must be marked experimental.

## 1. Philosophy

Mirror is a framework for building web products. It is a chassis for
pipelines, workers, middleware, and storage adapters. Mirror Core MUST stay
capability-agnostic.

Mirror is not a monolithic crawler. It is not a scraper. It is not a dashboard
framework. It is the execution layer that web products run on.

## 2. Non-negotiable principles

| Principle | Meaning |
| --- | --- |
| Core knows nothing | `mirror_core` imports no capability-specific package. |
| Discovery, not hardcoding | Extensions are loaded from entry points. |
| Installed ≠ activated | Settings decide what is active. |
| Typed boundaries | Boundaries use typed models. No raw dictionaries across subsystems. |
| Capability owns provider | Capabilities define contracts; providers implement them. |
| DAG, not list | Pipelines are directed acyclic graphs. |
| Deterministic configuration | Defaults → file → environment → runtime. |
| Transactional lifecycle | Startup rolls back on failure; shutdown reverses startup. |
| Observability first-class | Signals, middleware, and logs are built in. |

## 3. Current package topology

```
packages/
├── mirror_core/            # Chassis and runtime kernel
├── mirror_fetch/           # Fetch capability contract
├── mirror_fetch_httpx/     # HTTPX fetch provider
├── mirror_fetch_playwright/# Playwright fetch provider
├── mirror_archive/         # Archive capability contract
├── mirror_archive_warc/    # WARC archive provider
├── mirror_middleware/      # Core middleware implementations
├── mirror_cli/             # CLI interface and scaffolding
└── mirror_testing/         # Contract-testing utilities
```

## 4. Current core subsystems

| Subsystem | Responsibility |
| --- | --- |
| Application | Composition root. Owns registry, settings, signals, middleware, execution engine, lifecycle. |
| Registry | Stores discovered descriptors. |
| Discovery | Loads entry points and classifies descriptors. |
| Settings | Deterministic precedence and redaction rules. |
| Lifecycle | Transactional startup and reverse-order shutdown. |
| Signals | Observable lifecycle and execution events. |
| Middleware | Middleware chain around capability invocation. |
| Pipeline | DAG model for work. |
| Planner | Validates graph and produces execution plans. |
| Executor | Runs plans with isolated execution state. |
| Resource | Immutable provenance-bearing resource envelopes. |
| Worker contracts | Protocols for local and distributed execution. |

## 5. Dependency rules

```
capability -> mirror_core
provider -> capability
provider -> mirror_core
interface -> mirror_core
interface -> capability (optional for generation)
```

No cycles. No capability package may import a provider package.

## 6. Deferred to beta

- distributed workers
- dashboard / Django control plane
- REST and GraphQL interfaces
- production scheduler backend
- SaaS multi-tenancy
- billing
- cluster orchestration

## 7. Documentation rule

If a behavior is promised, it must appear in code, tests, and docs. If any one
is missing, the promise is incomplete.
