# CLI reference

## `mirror startproject <name>`

Create a Django-style Mirror project scaffold.

## `mirror startapp <name>`

Create an application package under `apps/` inside an existing project.

## `mirror doctor`

Inspect the current project directory and report whether the scaffold looks
healthy.

## `mirror list-capabilities`

Print the discovered capability descriptors.

## `mirror list-providers`

Print the discovered provider descriptors.

## `mirror status`

Print a simple application status summary.

## `mirror worker`

Start the default local worker backend for alpha development.

## `mirror run`

Run a pipeline or start the runtime from the current project settings.
When a pipeline file is supplied, Mirror loads it and executes the compiled DAG.
When no pipeline file is supplied, Mirror starts and stops the configured runtime as a health check.
