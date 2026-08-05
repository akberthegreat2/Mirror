# Contributing to Mirror

Mirror is a modular application framework. The repository is the source of truth.

## Before you change code

- Read `docs/ARCHITECTURE.md`.
- Read `docs/ROADMAP.md`.
- Read `docs/ALPHA_CONTRACT.md`.
- Read `docs/EXECUTION_SEMANTICS.md`.
- Read `docs/MIDDLEWARE_CONTRACT.md`.
- Read `docs/WORKER_CONTRACT.md`.
- Read `docs/SIGNAL_CONTRACT.md`.
- Read `docs/RELEASE_CHECKLIST.md`.
- Read `docs/CONSTITUTION.md`.
- Read the relevant ADRs in `docs/adr/`.
- Keep `mirror_core` capability-agnostic.
- Add or update tests for every behavior change.
- Update docs for every public API or developer-facing command.

## Required checks

Run the full test suite before sending a change:

```bash
pytest
```

When available in your environment, also run:

```bash
ruff check .
ruff format --check .
mypy --strict .
```

## Public API rules

- Use Google-style docstrings.
- Keep types explicit.
- Prefer immutable descriptors and models.
- Document any new architecture decision in an ADR.
- Add a PR note when the change affects behavior.

## Project structure

`mirror startproject` creates a runnable project skeleton.
`mirror startapp` creates a reusable application app skeleton.
`mirror doctor` validates the scaffold and runtime prerequisites.
`mirror worker` starts the local worker contract implementation.
