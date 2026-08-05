# Mirror

Mirror helps you build crawlers, archives, monitors, and other web products in Python.

Use Mirror when you want to:

- discover and save URLs;
- fetch pages with different backends;
- archive content for later;
- retry work automatically;
- run jobs locally first, then grow into workers later;
- build a SaaS or internal tool around web data.

Mirror is built as a small core plus optional packages. You install only the parts you need.

## What you can build

| Example | What Mirror gives you |
|---|---|
| Website crawler | Discover URLs, fetch pages, and keep the results |
| Web archive | Store HTML, WARC, JSON, or other captured content |
| Change monitor | Check pages on a schedule and compare results |
| SEO tool | Crawl pages and keep a history of what changed |
| Automation job | Run repeatable web work with retries and logs |

## Quick start

```bash
pip install -e .[dev]

mirror startproject demo
cd demo

mirror doctor
mirror startapp monitor
```

If you are working inside the monorepo checkout, the helper files in the
repository root make the packages importable without extra setup.

## What ships in this repository

| Package | Purpose |
|---|---|
| `mirror-core` | Discovery, registries, lifecycle, planner, executor, resources, signals, middleware contracts |
| `mirror-fetch` | Fetch capability contract |
| `mirror-fetch-httpx` | HTTPX fetch backend |
| `mirror-fetch-playwright` | Playwright browser fetch backend |
| `mirror-archive` | Archive capability contract |
| `mirror-archive-warc` | WARC archive backend |
| `mirror-middleware` | Retry, timeout, rate-limit, logging, and tracing middleware |
| `mirror-cli` | Project scaffolding and command-line tools |
| `mirror-testing` | Contract-test helpers for providers and middleware |

## Read next

- `docs/README.md` — documentation map
- `docs/getting-started/quickstart.md` — the shortest path to a first project
- `docs/ARCHITECTURE.md` — contributor contract and repository rules
- `docs/CONSTITUTION.md` — documentation and contribution rules
- `docs/adr/README.md` — architecture decisions
- `docs/ALPHA_CONTRACT.md` — what “alpha” means in this repository
