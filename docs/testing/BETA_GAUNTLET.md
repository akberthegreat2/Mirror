# Beta certification gauntlet

Phase D turns the existing test suite into an explicit release gate. The goal
is not to claim that an offline sandbox is a production deployment. The goal is
to make every boundary that can be certified offline mechanically testable and
to leave external infrastructure gates explicit.

## Offline gates

1. **Lint** — `ruff check .` and `ruff format --check .`.
2. **Static typing** — `mypy` over every `src` tree using the repository's
   strict configuration. Frameworks without bundled typing metadata are treated
   as explicit integration boundaries in the mypy configuration.
3. **Unit/contract suite** — `pytest -q`.
4. **Manifest certification** — every capability/provider/interface entry point
   resolves to its published manifest.
5. **Django migration/admin smoke** — the control-plane package can migrate its
   schema and load its admin registrations.
6. **Pipeline repository smoke** — managed pipeline blobs round-trip through
   Core's pipeline model and retain immutable version history.

## External gates

A release still requires real infrastructure for:

- PostgreSQL worker/backend integration;
- Redis broker communication;
- a real Celery worker process;
- real Scrapy execution;
- WARC provider execution with `warcio`;
- Playwright browser execution where that provider is selected.

These tests are marked or documented as integration/lab tests. They must not be
replaced with local shims merely to make CI green.

## Expected release evidence

A release handover should include:

```text
ruff check .                  -> clean
ruff format --check .        -> clean
mypy ...                     -> clean
pytest -q                    -> clean, with explicit external skips
manifest certification      -> clean
Django migration smoke      -> clean
live PostgreSQL certification -> performed in CI/lab
live Redis/Celery            -> performed in CI/lab
```

The exact counts are recorded in the handover rather than treated as a
permanent promise, because package and test counts change over time.
