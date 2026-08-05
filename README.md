# Mirror

Mirror helps you build crawlers, web archives, monitors, schedulers, and web-
data SaaS products in Python.

Use Mirror when you need to:

- crawl sites and save discovered URLs;
- archive pages and responses;
- monitor pages for changes;
- run recurring jobs with workers and a scheduler;
- build a web control plane with Django admin;
- keep the business logic separate from the backend implementation.

Mirror splits the problem into:

- a capability-agnostic core;
- installable capabilities such as fetch and archive;
- replaceable providers such as HTTPX and Playwright;
- middleware, worker contracts, signals, storage contracts, and the Django control plane package.

## Quick start

```bash
pip install -e .[dev]

mirror startproject demo
cd demo
mirror doctor
mirror startapp monitor
mirror worker
```

If you are working from the monorepo checkout, the repository root contains two
bootstrap files that keep the packages importable without a prior editable
install:

- `conftest.py` for pytest;
- `sitecustomize.py` for plain Python sessions.

Read the explanation here: `docs/reference/testing_bootstrap.md`.

## What lives where

- `docs/ARCHITECTURE.md` — the contributor-facing architecture contract.
- `docs/ROADMAP.md` — delivery phases and current status.
- `docs/ALPHA_CHECKLIST.md` — the frozen alpha checklist.
- `docs/BETA_CONTRACT.md` — the beta runtime contract.
- `docs/ALPHA_CONTRACT.md` — the release contract for contributors.
- `docs/EXECUTION_SEMANTICS.md` — runtime behavior and terminal states.
- `docs/MIDDLEWARE_CONTRACT.md` — middleware scopes and guarantees.
- `docs/WORKER_CONTRACT.md` — worker contracts and implementations.
- `docs/SIGNAL_CONTRACT.md` — signal names and observability rules.
- `docs/RELEASE_CHECKLIST.md` — the checks before tagging a release.
- `docs/FUTURE.md` — deferred and experimental ideas.
- `docs/PRs/` — implementation notes for the major phases.
- `packages/mirror_control_django/` — the Django control-plane contract package.
- `docs/adr/` — architecture decision records.
- `CONTRIBUTING.md` — contributor workflow and quality requirements.
- `docs/README.md` — the documentation index.
- `docs/concepts/` — framework concepts.
- `docs/tutorials/` — step-by-step guides.
- `docs/reference/` — command and package reference.
- `docs/implementation/` — implementation notes and phase summaries.

## Developer workflow

The main developer commands are:

```bash
mirror startproject demo
mirror startapp monitor
mirror doctor
mirror list-capabilities
mirror list-providers
mirror worker
mirror run
```

The `startproject` command creates a runnable project scaffold with:

- `manage.py`
- `config/settings.py`
- `config/asgi.py`
- `config/wsgi.py`
- `config/urls.py`
- `apps/core/`
- `apps/core/workers.py`
- `tests/`
- `docs/`

The `startapp` command adds a reusable application package under `apps/`.

## Verification

Run the test suite from the repository root:

```bash
pytest
```

The repository includes smoke tests that exercise real package imports, the
project scaffold commands, the doctor command, worker contracts, and a
provider-swap integration for Fetch.
