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

Initialize the default local worker backend and confirm it is ready.

Use `--backend inline` for the in-memory backend or `--backend sqlite` for the durable local backend.


## `mirror run`

Load the configured settings and optionally a pipeline file, then start the
runtime and execute the pipeline.
