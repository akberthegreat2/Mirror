# Quickstart

Mirror is for people who want to crawl websites, keep the results, and build
something useful on top.

## 1. Create a project

```bash
mirror startproject demo
cd demo
```

## 2. Check that the scaffold is healthy

```bash
mirror doctor
```

## 3. Start the local worker

```bash
mirror worker
```

## 4. Add an app

```bash
mirror startapp monitor
```

## What you should see

- a `manage.py` file in the project root
- a `config/` folder with settings and entry points
- an `apps/` folder for reusable work
- a `docs/` folder for project notes

That is enough to start building a real Mirror project.
