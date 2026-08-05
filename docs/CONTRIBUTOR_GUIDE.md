# Contributor Guide

This guide is for maintainers and future contributors.

## Read first

1. `README.md`
2. `CONSTITUTION.md`
3. `ARCHITECTURE.md`
4. `ROADMAP.md`
5. `ALPHA_CONTRACT.md`
6. `EXECUTION_SEMANTICS.md`
7. `MIDDLEWARE_CONTRACT.md`
8. `WORKER_CONTRACT.md`
9. `SIGNAL_CONTRACT.md`
10. The relevant ADRs
11. The relevant package README

## Rules

- Keep `mirror_core` capability-agnostic.
- Add or update tests for every behavior change.
- Update docs for every public API or developer-facing command.
- Record architectural decisions in ADRs.
- Keep user docs friendly.
- Keep architecture docs strict.
- Keep reference docs exact.

## Required quality gates

Run the test suite before sending a change:

```bash
pytest
```

When available in your environment, also run:

```bash
ruff check .
ruff format --check .
mypy --strict .
```

## Release rule

If a promise is not documented and tested, it is not finished.
