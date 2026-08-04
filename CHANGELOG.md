# Changelog

## 0.1.0-alpha candidate — 2026-08-04

- Hardened WARC lifecycle, record semantics, concurrency, rotation, and errors.
- Removed skipped placeholder provider-contract tests.
- Added deterministic WARC contract coverage without external dependencies.
- Validated 98 tests, all package wheels, installed imports, entry points, and CLI.

## 0.1.0-alpha - Unreleased

### Added
- Real Playwright provider with explicit browser installation requirements.
- Typed `ArchivePayload` contract.
- `ComponentManager` as provider lifecycle owner.
- Dynamic dependency-ready DAG scheduling.
- Enforced step retry, timeout, and task cancellation.
- CLI runtime-input files and truthful `worker-check` command.
- WARC locking, async thread boundary, idempotent lifecycle, typed inputs, and file rotation.

### Changed
- Removed unsupported `fallback` from the alpha error-policy model.
- Reduced `mirror_core` root exports; provisional worker contracts remain under `mirror_core.workers`.
- Normalized the `mirror-testing` distribution name and dependencies.
- Corrected type-port assignability direction.

### Fixed
- Misleading workspace installation instructions.
- Fake Playwright implementation based on `urllib`.
- WARC self-start, concurrent writes, filename collisions, and unlimited segments.
- CLI commands that silently succeeded without performing their advertised work.

## [0.1.0-alpha] - 2026-08-04

### Added
- Isolated execution runs and structured terminal outcomes.
- Configuration-driven provider swapping for HTTPX and Playwright.
- Runtime input support in the CLI.
- Typed Archive payloads and WARC rotation controls.
- Alpha contract, implementation report, validation record, and known-limitations documentation.

### Changed
- Provider lifecycle ownership moved into `ComponentManager`.
- DAG execution starts steps when their own dependencies are complete.
- Retry, timeout, and cancellation now have real runtime semantics.
- Public error policies are limited to implemented behavior.
- Root public exports no longer promote provisional worker contracts.
- Installation documentation now reflects the monorepo package layout.

### Fixed
- Unsafe port assignability direction.
- Incorrect resource parent lineage and producer identity.
- Misleading Playwright provider implementation.
- WARC event-loop blocking, concurrent writes, non-idempotent setup, and unlimited file growth.
- CLI runtime-input omission and misleading worker command.

### Deferred
- Distributed worker execution, production lease semantics, remote storage providers, and optional web interfaces.
