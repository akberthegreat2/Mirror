# Developer experience

Mirror uses a Django-style project scaffold so you start from a known layout
instead of inventing one for every app.

## What `mirror startproject` gives you

- `manage.py` for project-local commands
- `config/settings.py` for project settings
- `config/asgi.py` and `config/wsgi.py` for future interface hooks
- `config/urls.py` for future routing hooks
- `apps/core/` as the default app bundle
- `tests/` for project tests
- `docs/` for project notes and decisions

## What `mirror startapp` gives you

- `config.py`
- `pipelines.py`
- `tasks.py`
- `middleware.py`
- `signals.py`
- `workers.py`
- `README.md`
- `tests.py`

## Why it helps

Mirror keeps the layout stable even when the internals change. That makes it
easier to add new products, swap backends, and hand the project to another
contributor later.
