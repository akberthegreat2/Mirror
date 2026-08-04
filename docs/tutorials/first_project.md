# Tutorial: create a Mirror project

This tutorial shows the minimal path from a fresh install to a runnable project
scaffold.

## 1. Install Mirror

```bash
make install
```

## 2. Create a project scaffold

```bash
mirror startproject demo
cd demo
```

## 3. Inspect the scaffold

You should see:

- `manage.py`
- `config/settings.py`
- `config/asgi.py`
- `config/wsgi.py`
- `apps/core/`
- `apps/core/workers.py`
- `tests/`
- `docs/`

## 4. Run the project doctor

```bash
mirror doctor
```

The doctor command validates that the scaffold is present and that the core
packages import correctly.

## 5. Add an application package

```bash
mirror startapp monitor
```

The app scaffold lives under `apps/monitor/` and is ready for pipelines,
middleware, signals, workers, and app-specific tests.
