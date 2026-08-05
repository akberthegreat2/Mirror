# Mirror

Mirror helps you crawl websites, save discovered URLs, archive pages, retry failures, and run recurring jobs from Python.

Use Mirror when you want to build:

- a website crawler that keeps the URLs it finds
- an archive service that stores pages and responses
- a monitor that checks for change over time
- an SEO or content platform on top of Django
- a web SaaS that needs workers, scheduling, and storage

Mirror splits the problem into a few small parts:

- **pipelines** describe the work
- **capabilities** define the contract
- **providers** choose the implementation
- **middleware** adds retries, logging, tracing, and rate limits
- **workers** run the jobs
- **storage** remembers metadata and blobs

## Quick start

```bash
pip install -e .[dev]

mirror startproject demo
cd demo
mirror doctor
mirror worker
```

You can start a reusable app inside the generated project:

```bash
mirror startapp monitor
```

And you can run a pipeline from a settings file:

```bash
mirror run --config config/settings.toml --pipeline pipelines/crawl.toml
```

## What is already included

- `mirror-core` — the capability-agnostic runtime kernel
- `mirror-fetch` — fetch capability contract
- `mirror-fetch-httpx` — HTTPX fetch provider
- `mirror-fetch-playwright` — Playwright-style fetch provider
- `mirror-archive` — archive capability contract
- `mirror-archive-warc` — WARC archive provider
- `mirror-middleware` — retry, timeout, rate limit, logging, and tracing middleware
- `mirror-crawl` — crawl capability and local provider
- `mirror-cli` — scaffold, doctor, run, worker, and discovery commands
- `mirror-testing` — helper contracts for provider tests

## Documentation

- `docs/README.md` — documentation map
- `docs/BETA_CONTRACT.md` — beta runtime contract
- `docs/ARCHITECTURE.md` — contributor-facing framework contract
- `docs/ALPHA_CONTRACT.md` — frozen alpha release contract
- `docs/RELEASE_CHECKLIST.md` — what must pass before tagging

Mirror's architecture is intentionally split so the framework stays stable while
implementations can change.
