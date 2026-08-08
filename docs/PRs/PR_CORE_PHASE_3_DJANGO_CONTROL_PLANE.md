# PR: Phase three Django control plane

## Problem

Mirror needs a real operator surface. The framework can already execute work,
but users still need a place to inspect runs, crawled URLs, archives, workers,
schedules, and pipeline versions.

## Decision

Implement a reusable Django control-plane app and a separate REST control-plane
package on top of Mirror's manifest catalog and pipeline repository contracts.
Mirror Core remains Django-free.

## Status

Implemented. The remaining work is live deployment/lab validation and future
application-specific authorization policy.

## What this snapshot provides

- control-plane ADRs and docs that describe the desired boundary;
- a shared control-plane manifest catalog;
- Django model classes and admin registrations;
- a blob-backed pipeline repository;
- REST serializers, viewsets, and router;
- tests that keep the boundary explicit.

## Validation

- the design stays optional and core-agnostic;
- the repository can still be used and tested without Django in the core kernel;
- the Django and REST packages can be mounted into an existing Django project.

## Remaining work

- richer dashboard UX;
- auth/roles wiring;
- project scaffolding commands for new deployments;
- integration tests against a real PostgreSQL control-plane database.
