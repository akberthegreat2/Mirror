# PR: Pre-alpha contract and release hardening

## Purpose

Make the repository's public claims match its implementation before tagging `v0.1.0-alpha`.

## Runtime changes

- Added `ComponentManager` and moved provider lifecycle ownership out of `Application`.
- Replaced level barriers with dependency-ready DAG scheduling.
- Enforced typed retry policies, timeouts, and actual asyncio task cancellation.
- Removed unsupported fallback policy.
- Corrected source-to-target port assignability.
- Reduced unstable worker exports.

## Provider changes

- Replaced the urllib-based "Playwright-style" provider with a real Playwright browser provider.
- Added clear failure when browsers have not been installed.
- Introduced typed `ArchivePayload`.
- Made WARC lifecycle idempotent, writes concurrency-safe, I/O offloaded, metadata sanitized, and files rotatable.

## CLI and packaging

- `mirror run` now requires a pipeline and accepts an explicit runtime-input file.
- Replaced misleading `worker` command with `worker-check`.
- Normalized `mirror-testing` distribution metadata.
- Removed generated build artifacts.
- Corrected root installation and release instructions.

## Validation

- 86 tests pass; 2 WARC tests are skipped when `warcio` is unavailable.
- Every package builds into a wheel with `pip wheel --no-deps --no-build-isolation`.
- Python source compilation passes.

## Explicitly deferred

- Durable distributed workers and leases.
- S3/GCS/Azure storage providers.
- Dashboard, REST, and Admin interfaces.
- Schema migration registry and durable payload reconstruction.

These remain extension contracts or roadmap items, not alpha claims.
