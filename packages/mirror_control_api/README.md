# mirror-control-api

`mirror-control-api` is Mirror's REST interface for the control plane. It
exposes the same control-plane objects used by Django admin, but as an API
that can be mounted into an existing Django project or served on its own.

## What it provides

- DRF serializers for the control-plane models;
- model viewsets and routers;
- a manifest endpoint for interface discovery;
- a shared contract with the Django admin surface.
