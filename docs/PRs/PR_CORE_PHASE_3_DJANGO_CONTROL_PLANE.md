# PR: Phase three Django control plane

## Problem

Mirror needs a real operator surface. The framework can already execute work,
but users still need a place to inspect runs, crawled URLs, archives, workers,
and schedules.

## Decision

Document the future Django control-plane boundary without moving any of that
responsibility into Mirror Core.

## What this snapshot provides

- control-plane ADRs and docs that describe the desired boundary;
- a Django settings-fragment contract on paper;
- metadata and admin model specs for projects, runs, steps, workers,
  schedules, crawled URLs, archive records, and checkpoints;
- tests and docs that keep the boundary explicit even while the package itself
  remains out of this snapshot.

## Validation

- the design stays optional and core-agnostic;
- the repository can still be used and tested without Django installed.

## Deferred

- real Django model classes and admin registrations;
- auth/roles wiring;
- control-plane UI pages;
- Django integration tests once Django is available in the environment.
