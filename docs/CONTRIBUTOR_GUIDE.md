# Contributor Guide

This guide is the entry point for new contributors and future reasoning models.

## Read first

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ROADMAP.md`
4. `docs/ALPHA_CHECKLIST.md`
5. `docs/ALPHA_CONTRACT.md`
6. `docs/BETA_CONTRACT.md`
7. `docs/EXECUTION_SEMANTICS.md`
8. `docs/MIDDLEWARE_CONTRACT.md`
9. `docs/WORKER_CONTRACT.md`
10. `docs/SIGNAL_CONTRACT.md`
11. `docs/adr/README.md`
12. The relevant PR note in `docs/PRs/`
13. The relevant package README

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
