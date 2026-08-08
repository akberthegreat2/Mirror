# mirror-control-api

`mirror-control-api` is Mirror's REST control-plane app. It exposes the same
control-plane objects that the Django admin surface manages, but as a DRF API
that can be mounted into an existing Django project or served on its own.

## What it ships

- REST serializers for all control-plane models;
- model viewsets for projects, pipelines, versions, runs, steps, workers,
  schedules, crawled URLs, archives, checkpoints, and dead letters;
- a manifest endpoint that mirrors the shared control-plane catalog;
- a router that can be included in an existing Django URL configuration.

## Endpoints

- `/manifest/`
- `/projects/`
- `/pipelines/`
- `/pipeline-versions/`
- `/runs/`
- `/steps/`
- `/workers/`
- `/schedules/`
- `/crawled-urls/`
- `/archives/`
- `/checkpoints/`
- `/dead-letters/`

## Use cases

- embed the API in an existing Django project;
- expose Mirror control-plane state to another UI;
- drive automation without using Django admin directly.
