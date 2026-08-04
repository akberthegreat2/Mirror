# Mirror

**Composable web-infrastructure framework for Python.**

Mirror separates stable capability contracts from replaceable providers. Applications describe work as typed DAG pipelines; installed capability and provider packages are discovered at runtime; `mirror-core` remains domain-agnostic.

> **Status:** `v0.1.0-alpha` candidate. The local execution kernel, Fetch providers, middleware, CLI runner, and Archive/WARC reference path are implemented and tested. Distributed workers, remote artifact stores, dashboards, and additional capabilities remain experimental or future work.

## Why Mirror

Business code should depend on **what** it needs, not **how** it is implemented. A pipeline using the Fetch capability can select HTTPX today and Playwright later without rewriting the pipeline.

```python
settings = MirrorSettings(components={"fetch": {"provider": "httpx"}})
# Change only "httpx" to "playwright" to select browser rendering.
```

## Packages

| Distribution | Purpose |
|---|---|
| `mirror-core` | Discovery, registries, lifecycle, planner, executor, resources, signals, middleware contracts |
| `mirror-fetch` | Fetch capability contract and runner |
| `mirror-fetch-httpx` | HTTPX Fetch provider |
| `mirror-fetch-playwright` | Real Playwright browser Fetch provider |
| `mirror-archive` | Typed Archive capability contract |
| `mirror-archive-warc` | Concurrent-safe, rotating WARC provider |
| `mirror-middleware` | Retry, timeout, rate-limit, logging, and tracing middleware |
| `mirror-cli` | Project scaffolding, discovery inspection, and pipeline execution |
| `mirror-testing` | Provider contract-test helpers; development-only |

## Install from this monorepo

The repository root is a workspace, not the runtime package. Install member packages explicitly:

```bash
make install
```

For a minimal Fetch application:

```bash
python -m pip install -e packages/mirror_core
python -m pip install -e packages/mirror_fetch
python -m pip install -e packages/mirror_fetch_httpx
```

For Playwright rendering:

```bash
python -m pip install -e packages/mirror_fetch_playwright
playwright install chromium
```

## Minimal pipeline

```python
import asyncio

from mirror_core import Application, MirrorSettings, Pipeline, Step


async def main() -> None:
    settings = MirrorSettings(
        components={"fetch": {"provider": "httpx"}},
        component_settings={"fetch": {"httpx": {"timeout": 30.0}}},
    )
    pipeline = Pipeline(
        id="fetch-homepage",
        inputs={"url": "str"},
        steps=[
            Step(
                id="fetch",
                capability="fetch",
                input={"url": "$pipeline.url"},
                timeout=30.0,
            )
        ],
    )

    async with Application(settings=settings) as app:
        result = await app.run_pipeline_detailed(
            pipeline,
            inputs={"url": "https://example.com"},
        )
        print(result.outcome.value)
        print(result.results["fetch"].payload.status_code)


asyncio.run(main())
```

## CLI

```bash
mirror list-capabilities
mirror list-providers
mirror run --config mirror.toml --pipeline pipeline.toml --inputs inputs.json
mirror worker-check
```

`worker-check` is intentionally diagnostic: distributed/background worker execution is not presented as complete in this alpha.

## Runtime guarantees in this alpha

- Core imports no domain capability or provider.
- Discovery rejects invalid and duplicate descriptors.
- Startup is transactional and shutdown follows ownership order.
- Provider compatibility and protocols are validated before execution.
- Pipelines are compiled before execution; the executor receives an immutable plan.
- Independent DAG branches start when their own dependencies finish.
- Runtime inputs are explicit and validated.
- Retry, timeout, cancellation, `abort`, `continue`, and `skip` semantics are enforced.
- Middleware can short-circuit provider invocation.
- Resources record producer identity, schema version, fingerprint, and direct parents.
- WARC writes are serialized, offloaded from the event loop, and rotated by configured limits.

## Experimental or deferred

The contracts in `mirror_core.workers` are provisional and are not exported from the root API. Durable distributed execution, leases, checkpoints, object-storage providers, REST/Admin interfaces, dashboards, and additional capabilities are not claimed as complete.

## Development

```bash
make install
make check
make wheels
```

The release gate requires:

```bash
ruff check .
ruff format --check .
mypy packages/*/src
pytest
```

See [ARCHITECTURE.md](ARCHITECTURE.md), [docs/ALPHA_CONTRACT.md](docs/ALPHA_CONTRACT.md), and [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).

## License

MIT. See [LICENSE](LICENSE).
