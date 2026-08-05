# CLI reference

## `mirror startproject <name>`

Create a project scaffold with a `manage.py` file, config directory, app
directory, tests, and docs.

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

Reserved for pipeline execution. In this alpha snapshot it is still treated as
an experimental command and should not be used as the primary user workflow.
