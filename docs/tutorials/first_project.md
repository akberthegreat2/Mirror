# Tutorial: build your first Mirror project

This tutorial shows the shortest path from a fresh install to a working
Mirror project.

## 1. Install Mirror

```bash
pip install -e .[dev]
```

## 2. Create a project

```bash
mirror startproject demo
cd demo
```

## 3. Check that the scaffold is healthy

```bash
mirror doctor
```

You should see a clean report for the generated project.

## 4. Add an app

```bash
mirror startapp monitor
```

The app lives under `apps/monitor/` and gives you a place for pipelines,
middleware, signals, and workers.

## 5. What to do next

- write a pipeline;
- choose a provider;
- add tests;
- update the project docs.

Mirror keeps the framework pieces out of your business logic so you can focus on
what the project does.
