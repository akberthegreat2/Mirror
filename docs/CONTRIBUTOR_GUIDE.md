# Contributor Guide

This guide is the entry point for new contributors and future reasoning models.

## Read first

1. `README.md`
2. `ARCHITECTURE.md`
3. `ROADMAP.md`
4. `ALPHA_CHECKLIST.md`
5. `docs/ALPHA_CONTRACT.md`
6. `docs/EXECUTION_SEMANTICS.md`
7. `docs/MIDDLEWARE_CONTRACT.md`
8. `docs/WORKER_CONTRACT.md`
9. `docs/SIGNAL_CONTRACT.md`
10. The relevant ADRs
11. The relevant package README

## What to change

- Keep `mirror_core` capability-agnostic.
- Add tests with every behavior change.
- Update docs for every public API or developer command.
- Record architectural decisions in ADRs.
- Record behavior changes in PR notes.

## What not to change casually

- package boundaries;
- discovery namespaces;
- runtime contract shape;
- middleware semantics;
- worker semantics;
- signal semantics;
- configuration precedence.

## Required quality gates

When available in your environment, run:

```bash
pytest
mypy --strict .
ruff check .
ruff format --check .
```

## Release rule

If a promise is not documented and tested, it is not finished.
