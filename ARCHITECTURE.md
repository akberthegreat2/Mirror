# Mirror Architecture Specification

**Version:** 1.0
**Status:** Approved
**Date:** 2026-08-03

---

## 1. Philosophy

**Mirror is an application framework for building web infrastructure.**

It is not a crawler. It is not a scraper. It is a chassis that hosts capabilities and providers.

Users build applications by composing capabilities, not by customizing a monolithic tool.

---

## 2. Non‑Negotiable Principles

| Principle | Meaning |
|-----------|---------|
| **Core knows nothing** | `mirror_core` has no knowledge of HTTP, HTML, archives, or any domain. It imports no capability package. |
| **Discovery, not hardcoding** | All extensions are discovered via entry points. No hardcoded lists of capabilities, providers, or commands. |
| **Installed ≠ Activated** | Installing a package does not activate it. Settings decide which components are active. |
| **Typed boundaries** | All data passing between components is typed (Pydantic models). No dictionaries. |
| **Capability owns provider** | Capability defines the contract. Provider implements it. Capability never imports provider. |
| **DAG, not list** | Pipelines are directed acyclic graphs, not ordered lists. |
| **Deterministic configuration** | Settings follow a fixed precedence: defaults → file → environment → runtime. |
| **Transactional lifecycle** | Startup is all-or-nothing. Partial startup rolls back. Shutdown reverses initialization order. |
| **Observability first‑class** | Signals, middleware, and structured logging are built in, not bolted on. |

---

## 3. Package Topology

```
packages/
├── mirror_core/            # Chassis. Zero domain knowledge.
├── mirror-fetch/           # Capability: retrieve web resources.
├── mirror-fetch-httpx/     # Provider: HTTPX implementation.
├── mirror-fetch-firecrawl/ # Provider: Firecrawl implementation.
├── mirror-archive/         # Capability: persist resources.
├── mirror-archive-warc/    # Provider: WARC file writer.
├── mirror-storage/         # Capability: store and retrieve blobs.
├── mirror-storage-s3/      # Provider: Amazon S3.
├── mirror-cli/             # Interface: CLI discovery.
├── mirror-dashboard/       # Interface: Django admin integration.
└── mirror-testing/         # Contract testing utilities.
```

### Dependency Rules

```
capability ──> mirror_core
provider ──> capability
provider ──> mirror_core
interface ──> mirror_core
interface ──> capability (optional, for dynamic generation)
```

**No cycles.** Core has zero dependencies on any Mirror package.

---

## 4. Core Subsystems (`mirror_core`)

| Subsystem | Responsibility |
|-----------|----------------|
| **Application** | Composition root. Owns registry, settings, signals, middleware, execution engine. Manages lifecycle. |
| **Registry** | Stores discovered descriptors (`CapabilityConfig`, `ProviderConfig`, `MiddlewareConfig`, `InterfaceConfig`). |
| **Discovery** | Loads all `mirror` entry points, classifies descriptors, reports duplicates/errors. |
| **Settings** | Deterministic precedence (defaults → file → env → runtime). Secrets redacted. Frozen after validation. |
| **Lifecycle** | `AsyncLifecycle` protocol. Transactional startup. Reverse-order shutdown. Idempotent. |
| **Signals** | `SignalBus` with `emit()` and `subscribe()`. Sync/async receivers. Error policies. |
| **Middleware** | Middleware chain around capability invocation. Retry, timeout, rate limiting, tracing, etc. |
| **Pipeline** | DAG model: `Step` with `id`, `capability`, `input`, `outputs`, `condition`, `retry`, `timeout`, `on_error`. |
| **Planner** | Validates graph, detects cycles, topological sort, parallel groups. Produces `ExecutionPlan`. |
| **Executor** | Runs `ExecutionPlan` with bounded concurrency, cancellation, retries, state persistence. |
| **Resource** | `ResourceEnvelope` with `resource_id`, `resource_type`, `schema_version`, `payload`, `producer`, `parents`, `fingerprint`. |
| **Exceptions** | `MirrorError`, `ConfigurationError`, `LifecycleError`, `DiscoveryError`, `RegistryError`, `ValidationError`. |

---

## 5. Descriptors (Entry Point Metadata)

All extensions expose descriptors via the `mirror` entry point group.

### CapabilityConfig

```python
class CapabilityConfig:
    name: str
    api_version: str
    protocol: type[Protocol] | None
    request_model: type[BaseModel] | None
    result_model: type[BaseModel] | None
    settings_model: type[BaseModel] | None
    runner: Callable | None
    input_ports: dict[str, type[BaseModel]]
    output_ports: dict[str, type[BaseModel]]
    required_capabilities: list[str]
    optional_capabilities: list[str]
    signals: list[str]
    metadata: dict[str, Any]
```

### ProviderConfig

```python
class ProviderConfig:
    name: str
    capability: str
    capability_api: str  # version constraint
    factory: str         # import path
    settings_model: type[BaseModel] | str | None
    features: list[str]
    priority: int
    metadata: dict[str, Any]
```

### MiddlewareConfig

```python
class MiddlewareConfig:
    name: str
    factory: str
    settings_model: type[BaseModel] | str | None
    applies_to: list[str] | None
    ordering_constraints: dict[str, str] | None
    metadata: dict[str, Any]
```

### InterfaceConfig

```python
class InterfaceConfig:
    name: str
    interface_type: str  # "cli", "admin", "rest", "graphql"
    factory: str
    requires_capabilities: list[str]
    metadata: dict[str, Any]
```

---

## 6. Configuration

Settings follow deterministic precedence (later wins):

```
Model defaults
    ↓
Package defaults
    ↓
Configuration file (YAML/TOML/JSON)
    ↓
Environment variables (MIRROR_*)
    ↓
Runtime overrides
```

### Example `mirror.yaml`

```yaml
application:
  name: my-app
  environment: production

components:
  fetch:
    provider: httpx
    settings:
      timeout: 30
      user_agent: "Mirror/1.0"

middleware:
  global:
    - tracing
  fetch:
    - retry
    - rate_limit

secrets:
  api_key: "REDACTED"
```

- Secrets are redacted in logs, dumps, and reprs.
- All settings are frozen after validation.

---

## 7. Lifecycle

```python
class AsyncLifecycle(Protocol):
    async def setup(self) -> None: ...
    async def teardown(self) -> None: ...
```

Rules:
- `setup()` and `teardown()` are **idempotent**.
- `teardown()` is safe even if `setup()` partially failed.
- Startup is **transactional**: if any component fails, all previously set‑up components are torn down in reverse order.
- Shutdown reverses initialization order.
- No component may spawn background tasks that survive a call to `teardown()`.

---

## 8. Signals (Event Bus)

Core provides a `SignalBus` with:

- Named signals (e.g., `pipeline.started`, `step.succeeded`, `provider.initialized`)
- Synchronous and asynchronous receivers
- Ordered execution
- Error policies
- Disconnect support

Signals are for **observability** and **decoupled extension**. They must never alter business logic.

---

## 9. Middleware

Middleware wraps every capability invocation. It may:

- Transform requests or results
- Control flow (retry, timeout, rate limiting)
- Add cross‑cutting concerns (tracing, metrics, caching, authentication)

Middleware ordering is explicit and immutable after startup.

---

## 10. Pipeline (DAG)

A pipeline is a **Directed Acyclic Graph** of steps.

### Step Definition

```python
class Step:
    id: str
    capability: str
    provider: str | None  # optional, uses default from settings
    input: dict[str, str]  # bindings from other steps or pipeline inputs
    outputs: list[str]     # named outputs for other steps to consume
    condition: str | None  # safe expression language
    retry: RetryPolicy | None
    timeout: float | None
    on_error: ErrorPolicy  # abort, continue, skip, fallback
    metadata: dict[str, Any]
```

### Compilation

1. Validate step IDs and capability existence.
2. Validate input bindings point to existing outputs.
3. Build dependency graph (explicit + data dependencies).
4. Detect cycles (Kahn's algorithm).
5. Topologically sort nodes.
6. Group independent nodes for parallel execution.
7. Attach middleware, policies, and settings.
8. Produce immutable `ExecutionPlan`.

### Execution State Machine

```
PENDING → READY → RUNNING → SUCCEEDED
                    ├──→ RETRY_WAIT → READY
                    ├──→ FAILED
                    ├──→ CANCELLED
                    └──→ SKIPPED
```

---

## 11. Typed Resources

Every value passed between steps is a typed resource.

```python
class ResourceEnvelope(BaseModel):
    resource_id: UUID
    resource_type: str          # e.g., "FetchResult"
    schema_version: str
    payload: BaseModel          # capability‑specific model
    created_at: datetime
    producer: ProducerRef       # capability, provider, version, config
    parents: list[UUID]         # resources this depends on
    fingerprint: str            # deterministic hash of payload
    metadata: dict[str, Any]
```

### Large Payloads

Large payloads are represented as `BlobReference` (URI, checksum, size, media type). Execution metadata and small results remain inline.

### Provenance

Every output records:
- Producer identity (capability, provider, version)
- Configuration fingerprint
- Parent resources
- Timestamp

---

## 12. Exceptions

Core defines only generic exceptions:

```python
class MirrorError(Exception): ...
class ConfigurationError(MirrorError): ...
class LifecycleError(MirrorError): ...
class DiscoveryError(MirrorError): ...
class RegistryError(MirrorError): ...
class ValidationError(MirrorError): ...
```

Capability-specific errors (`FetchError`, `ArchiveError`) are defined in their respective packages and inherit from `MirrorError`.

---

## 13. Testing Strategy

- **Unit tests** live inside each package.
- **Contract tests** are provided by capability packages (e.g., `mirror_fetch.testing.FetchContract`).
- **Provider packages** run the contract tests against their implementation.
- **Integration tests** verify multiple capabilities work together.
- Tests must not require external internet unless explicitly marked.

---

## 14. Migration Plan

| Step | Action |
|------|--------|
| 1 | Create `mirror_core` with all engine subsystems. |
| 2 | Port `mirror-fetch` capability (protocol, models, runner, signals, contract tests). |
| 3 | Port `mirror-fetch-httpx` provider. |
| 4 | Port `mirror-cli` interface (dynamic command discovery). |
| 5 | Port `mirror-archive` + `mirror-archive-warc`. |
| 6 | Port `mirror-extract` + provider(s). |
| 7 | Port `mirror-storage` + providers. |
| 8+ | Additional capabilities, middleware, distributed schedulers. |

---

## 15. Public API Stability

- Only symbols exported from a package's root `__init__.py` and documented are public.
- Internal modules may change without notice during alpha.
- Breaking changes in `v0.x` must be documented in changelogs.
- At `1.0`, breaking changes require a deprecation window.

---

## 16. Non‑Goals (What Mirror Is Not)

| What It Is Not | Why |
|----------------|-----|
| A crawler framework | Crawling is a use case, not the core. |
| A scraping framework | Scraping is a use case. |
| A monolithic tool | It is a chassis. |
| A CLI‑first framework | CLI is an interface, not the core. |
| A web server | Admin/API interfaces are optional packages. |
| A batch processing system | Execution is abstract; schedulers are pluggable. |

---

## 17. Design Decisions (Recorded)

| Decision | Rationale |
|----------|-----------|
| Single entry point group (`mirror`) | Simpler discovery, no hardcoded categories. |
| Descriptors are metadata, not instantiated classes | Prevents import-time side effects, enables lazy loading. |
| Typed resources with envelopes | Enables validation, provenance, caching, serialization, contract testing. |
| DAG pipeline, not list | Supports branching, parallelism, conditions, retries. |
| Signals for observability | Decouples logging, metrics, tracing, dashboards. |
| Middleware for cross‑cutting concerns | Keeps capabilities clean. |
| Transactional lifecycle | Prevents partial startup. |
| Single `mirror` entry point | All extensions discoverable through one group. |

---

*This document is the source of truth. Code that conflicts with it is incorrect unless an accepted ADR changes the specification.*
