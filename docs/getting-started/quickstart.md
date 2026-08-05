# Quickstart

This is the fastest way to see Mirror working.

## 1. Install the repository

```bash
pip install -e .[dev]
```

## 2. Create a project

```bash
mirror startproject demo
cd demo
```

Mirror creates a familiar project layout with:

- `manage.py`
- `config/settings.py`
- `config/asgi.py`
- `config/wsgi.py`
- `config/urls.py`
- `apps/core/`
- `tests/`
- `docs/`

## 3. Check the scaffold

```bash
mirror doctor
```

`doctor` checks that the project structure looks healthy and that Mirror can see
the current project.

## 4. Add a reusable app

```bash
mirror startapp monitor
```

This adds an app under `apps/` for pipelines, tasks, middleware, signals, and
worker hooks.

## 5. Keep going

At this point you can add your own pipeline, choose a provider, and start
building a real web product.

Mirror is designed to stay out of your business logic while still handling the
repeated work around it.
