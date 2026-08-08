# Connect Mirror to the REST control plane

The REST control plane exposes the same objects as the Django admin surface, but
as API resources. This makes it useful for scripts, external dashboards, and
user interfaces that do not want to depend on Django admin directly.

## What you get

- a manifest endpoint;
- REST resources for projects, pipelines, pipeline versions, runs, steps,
  workers, schedules, crawled URLs, archives, checkpoints, and dead letters;
- a shared control-plane catalog with the Django app;
- the same blob-backed pipeline repository semantics used by the admin.

## Typical setup

1. Install Django, Django REST Framework, and `mirror-control-api`.
2. Add `mirror_control_api` to `INSTALLED_APPS` if you are using it directly.
3. Include `mirror_control_api.urls` in your Django URL configuration.
4. Run migrations for the control-plane models.
5. Consume the API from your automation or UI.

## Example requests

```bash
curl http://localhost:8000/manifest/
curl http://localhost:8000/pipelines/
curl http://localhost:8000/runs/
```

## Boundary

The API surfaces data; it does not replace Mirror Core's execution engine.
Pipelines are still compiled and executed by Mirror Core and its worker
contracts.
