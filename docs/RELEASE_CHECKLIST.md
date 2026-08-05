# Release Checklist

Use this checklist before tagging `v0.1.0`.

## Code checks

- [ ] `pytest`
- [ ] `mypy --strict .`
- [ ] `ruff check .`
- [ ] `ruff format --check .`

## Clean install checks

- [ ] Create a fresh virtual environment
- [ ] Install the workspace from source
- [ ] Run `mirror startproject demo`
- [ ] Run `cd demo`
- [ ] Run `python manage.py doctor`
- [ ] Run `python manage.py worker`
- [ ] Run `python manage.py run`

## Modularity checks

- [ ] `mirror-fetch-httpx` works
- [ ] `mirror-fetch-playwright` works
- [ ] The same fetch pipeline runs with either provider
- [ ] The pipeline definition does not change when the provider changes

## Documentation checks

- [ ] `README.md` is current
- [ ] `CONTRIBUTING.md` is current
- [ ] `CODE_OF_CONDUCT.md` is current
- [ ] `ROADMAP.md` is current
- [ ] `ALPHA_CHECKLIST.md` is current
- [ ] `docs/README.md` is current
- [ ] `docs/ARCHITECTURE.md` is current
- [ ] `docs/RELEASE_CHECKLIST.md` matches the actual release workflow

## Release rule

If a checklist item is not true in code, tests, or docs, do not tag the release.
