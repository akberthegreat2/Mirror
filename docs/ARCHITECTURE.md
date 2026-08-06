
# Mirror Architecture Specification

**Version:** 1.1
**Status:** Approved
**Date:** 2026-08-06

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
├── mirror_fetch_playwright/ # Playwright fetch provider
├── mirror_archive/         # Archive capability contract
├── mirror_archive_warc/    # WARC archive provider
├── mirror_crawl/           # Crawl capability contract
├── mirror_crawl_local/     # Local crawl provider
├── mirror_search/          # Search capability contract
├── mirror_search_memory/   # First-party search provider
├── mirror_analyze/         # Analyze capability contract
├── mirror_analyze_basic/   # First-party analyze provider
├── mirror_scrape/          # Scrape capability contract
├── mirror_scrape_basic/    # First-party scrape provider
├── mirror_diff/            # Diff capability contract
├── mirror_diff_text/       # First-party diff provider
├── mirror_monitor/         # Monitor capability contract
├── mirror_monitor_memory/  # First-party monitor provider
├── mirror_cli/             # CLI interface and scaffolding
├── mirror_control_django/  # Django control-plane bridge
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
| Middleware | Middleware chain owned by `mirror_core`. |
| Pipeline | DAG model for work. |
| Planner | Validates graph and produces execution plans. |
| Executor | Runs plans with isolated execution state. |
| Resource | Immutable provenance-bearing resource envelopes. |
| Worker contracts | Protocols for local and distributed execution. |
| Storage contracts | `MetadataStore`/`BlobStore` protocols plus in-memory, SQLite, and filesystem implementations. |
| Scheduler contract | `SchedulerBackend` protocol plus in-memory and SQLite implementations. |

## 5. Dependency rules

```
capability -> mirror_core
provider -> capability
provider -> mirror_core
interface -> mirror_core
interface -> capability (optional for generation)

Compatibility shims may exist temporarily, but the executable middleware implementation lives only in `mirror_core`.
```

No cycles. No capability package may import a provider package.

## 6. Deferred to beta

- distributed workers
- dashboard / Django control plane
- REST and GraphQL interfaces
- SaaS multi-tenancy
- billing
- cluster orchestration

## 7. Documentation rule

If a behavior is promised, it must appear in code, tests, and docs. If any one
is missing, the promise is incomplete.
