# Pipelines

A Mirror pipeline is a declarative DAG of capability steps. A pipeline is a
**definition**, not an execution. An execution is an immutable run created from
a particular pipeline definition.

## One-shot operations and reusable pipelines

Mirror supports both:

```bash
mirror run --pipeline crawl.json --inputs inputs.json
```

and reusable pipeline documents managed by an application or control plane.
A one-shot capability invocation can be represented internally as a one-step
execution without forcing the user to create a project or database.

## Code-defined pipelines

Python-defined pipelines remain valid for developers who want code as the
source of truth. Interfaces treat these definitions as read-only. Mirror does
not rewrite a developer's Python source code.

A code pipeline can be explicitly materialized into a managed pipeline:

```text
Python definition
      |
      | explicit materialization
      v
PipelineDefinition blob
      |
      +--> metadata/index in the configured database
```

Materialization is a deliberate operation. Deployment or application startup
must not silently rewrite an administrator-managed pipeline.

## Managed pipelines

Managed pipelines are documents stored through the configured blob/document
store. The database stores metadata such as identity, ownership, current
version, hashes, and references to the definition blob.

Each saved version is immutable. Editing a managed pipeline creates a new
version rather than mutating a version already used by an execution.

```text
website-intelligence
  v1 -> immutable blob
  v2 -> immutable blob
  v3 -> immutable blob
```

An execution records the exact pipeline version it compiled. A worker therefore
cannot accidentally execute a definition that changed after the job was
submitted.

## Policies

Execution behavior belongs to the pipeline/runtime policy model, not to
Celery, Redis, Django, or a provider.

Mirror resolves policy in layers:

```text
Global defaults
      |
Pipeline override
      |
Step override
```

The most specific applicable value wins. Policy objects can represent concerns
such as retry, timeout, failure handling, fallback, checkpointing, and future
runtime policies without coupling them to one infrastructure backend.

A step can explicitly say what should happen when it fails. For example:

```yaml
steps:
  - id: crawl
    capability: crawl
    on_error: abort

  - id: enrich
    capability: enrich
    on_error: continue
```

The executor enforces that semantic decision. Celery only transports the work.

## Interfaces

CLI, Django, and REST are different projections of the same pipeline model.
They should not invent separate pipeline semantics.

```text
CLI -----------+
Django ---------+--> Interface/Application layer --> Mirror Core
REST -----------+
                         |
                   PipelineDefinition
                         |
                    ExecutionPlan
                         |
                      Execution
```

The interface-neutral `mirror_core.interfaces.InterfaceCatalog` is the common
manifest projection used by interfaces to discover capabilities, providers,
and interfaces without importing one another.
