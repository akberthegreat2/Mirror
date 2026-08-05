# Developer experience

Mirror uses a Django-style project scaffold so contributors can start from a
known layout instead of inventing one for every application.

## The project scaffold

`mirror startproject <name>` creates a project directory with:

- `manage.py` for CLI entry points;
- `config/settings.py` for project-level Mirror configuration;
- `config/asgi.py` and `config/wsgi.py` as reserved interface hooks;
- `config/urls.py` as a reserved routing hook;
- `apps/core/` as the default application bundle;
- `apps/core/workers.py` as the default worker registration hook;
- `tests/` for project smoke tests;
- `docs/` for project-specific documentation.

## The app scaffold

`mirror startapp <name>` adds a reusable application package under `apps/`.
The generated app includes configuration, pipeline, middleware, signal, worker,
task, and smoke-test files.

## Workspace bootstrap

The repository root also contains two helper files that make the source checkout
pleasant to use:

- `conftest.py` adds every `packages/*/src` directory to pytest imports.
- `sitecustomize.py` does the same for plain Python sessions.

These files exist only to make source-checkout development easier. They are not
product features.

## Why this matters

The scaffold keeps the project layout stable while the runtime evolves. A future
contributor can add capabilities, providers, or interfaces without guessing where
project settings or app code should live.
