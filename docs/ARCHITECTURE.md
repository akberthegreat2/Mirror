# Architecture Specification

This file points to the frozen framework contract used by the repository.
The canonical architecture specification lives at the repository root in
`ARCHITECTURE.md`.

## Read this with the alpha contract

A contributor should read this file together with:

- `../ARCHITECTURE.md`
- `ALPHA_CONTRACT.md`
- `ROADMAP.md`
- `RELEASE_CHECKLIST.md`
- `CONTRIBUTOR_GUIDE.md`

## What this repository freezes

- `mirror_core` stays capability-agnostic.
- Discovery happens through entry points.
- Middleware belongs in the core contract.
- Workers belong in the core contract.
- Signals belong in the core contract.
- Runtime input values stay separate from pipeline input declarations.
- Execution is plan-driven, not discovery-driven.

## What is deferred to beta

- distributed workers
- dashboard and Django integration
- REST and GraphQL interfaces
- scheduling service
- SaaS multi-tenancy
- billing
- Kubernetes orchestration
- cluster scheduling
