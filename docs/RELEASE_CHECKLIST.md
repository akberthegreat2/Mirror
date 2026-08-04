# Release Checklist

Use this checklist before tagging `v0.1.0-alpha`.

## Code quality

- [x] `pytest` passes in the current review environment: **86 passed, 2 dependency-gated skips**.
- [ ] `ruff check .` passes in CI.
- [ ] `ruff format --check .` passes in CI.
- [ ] `mypy packages/*/src` passes in CI.
- [x] `python -m compileall` passes.

Ruff and mypy were unavailable in the review environment. They remain mandatory release gates rather than being silently waived.

## Package integrity

- [x] Every member package builds into a wheel with `pip wheel --no-deps --no-build-isolation`.
- [x] Core, Fetch, HTTPX, Middleware, and CLI wheels install together in an isolated virtual environment.
- [x] Imports resolve from installed wheels rather than workspace source paths.
- [x] Installed `mirror` entry points are discoverable.
- [x] Installed `mirror --help` succeeds.
- [x] The source archive contains no `build/`, `dist/`, `*.egg-info/`, `__pycache__/`, or test-cache directories.

## Runtime contracts

- [x] Core imports no domain capability or provider.
- [x] Startup is transactional and restartable.
- [x] Provider protocol and API compatibility are validated before execution.
- [x] Runtime inputs are explicit.
- [x] Retry and timeout policies are enforced.
- [x] Cancellation cancels active asyncio tasks.
- [x] Supported error policies are limited to implemented semantics: `abort`, `continue`, and `skip`.
- [x] Middleware short-circuiting is supported.
- [x] Direct resource parents and producer identities are recorded.
- [x] WARC setup is idempotent, writes are serialized, blocking I/O is offloaded, and rotation is supported.

## CLI checks

- [x] `mirror --help`
- [x] `mirror list-capabilities`
- [x] `mirror list-providers`
- [x] `mirror run --pipeline PIPELINE --inputs INPUTS`
- [x] `mirror worker-check` truthfully reports the worker subsystem as experimental.
- [ ] Run one real pipeline against a controlled endpoint in CI or a network-enabled release environment.

## Modularity checks

- [x] `mirror-core` builds independently.
- [x] `mirror-fetch` and `mirror-fetch-httpx` build independently.
- [x] HTTPX and Playwright satisfy the same Fetch capability contract.
- [x] Provider selection is configuration-driven; the pipeline contract does not change.
- [ ] Execute the same installed-wheel pipeline once with HTTPX and once with Playwright in browser-enabled CI.

## Documentation

- [x] Root README describes the real installation model and alpha scope.
- [x] Architecture and alpha-contract documents distinguish implemented, experimental, and deferred work.
- [x] Provider and package READMEs exist.
- [x] PR and validation records document the hardening work.
- [x] Known limitations are explicit.

## Release rule

Do not tag the alpha until all unchecked CI/environment-dependent items above have passed. Do not convert deferred subsystems into public claims merely because their protocols exist.
