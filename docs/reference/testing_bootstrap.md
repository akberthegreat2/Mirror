# Testing bootstrap

Mirror keeps the repository importable from a source checkout by using two small
bootstrap files at the repository root:

- `conftest.py` for pytest;
- `sitecustomize.py` for plain Python sessions and ad hoc scripts.

## `conftest.py`

Pytest loads this file before it imports package tests. The file adds each
`packages/*/src` directory to `sys.path` so test runs can import the workspace
packages without requiring a prior editable install.

## `sitecustomize.py`

Python imports `sitecustomize.py` automatically when it is present on the import
path. Mirror uses it to make source-checkout scripts behave like a workspace
checkout instead of a half-installed environment.

## Why both exist

- `conftest.py` makes the test suite self-contained.
- `sitecustomize.py` makes local scripts and interactive debugging easier.

## What they are not

They are not runtime features. They do not ship business logic. They only make
source-checkout development easier.
