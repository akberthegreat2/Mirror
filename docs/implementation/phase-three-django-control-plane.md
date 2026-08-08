# Phase three: Django control plane

**Status:** Implemented in this snapshot as reusable Django and REST packages.

## Goal

Give Mirror a Django-based control plane for metadata, users, admin pages, and
operator workflows without moving any of that responsibility into Mirror Core.

## Implemented here

- control-plane manifest catalog;
- Django models and admin registrations;
- blob-backed pipeline repository;
- dashboard summary view;
- REST API with serializers, viewsets, and router;
- optional embedding into an existing Django project;
- package-level smoke tests.

## Still to do

- richer dashboard pages and filters;
- user/role/permission policy wiring;
- more project scaffolding helpers for new deployments;
- end-to-end integration tests against a real PostgreSQL control-plane DB.

## Non-goals

- Mirror Core MUST NOT import Django.
- Mirror Core MUST NOT depend on any control-plane models.
- The control plane MUST remain replaceable at the package boundary.
