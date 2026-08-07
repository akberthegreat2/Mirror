# Mirror Alpha Contract

This document is the release contract for the frozen alpha. A new contributor
or reasoning model should be able to read this file, the architecture spec, the
roadmap, and the ADRs without relying on chat history.

## What alpha means

Mirror reaches alpha when the repository satisfies all of the following:

- `mirror_core` stays capability-agnostic.
- Discovery happens through entry points.
- Middleware is a core contract.
- Worker contracts are in core.
- Signals are a core contract.
- `mirror startproject` works in a clean environment.
- `mirror startapp` works in a clean environment.
- `mirror doctor` validates the scaffold.
- One capability can swap between two providers without changing the pipeline.
- The repository explains itself through docs, ADRs, and PR notes.
- The documented release checks pass in a local development environment.

## Frozen runtime guarantees

Mirror core must provide:

- typed descriptors and typed execution boundaries;
- a pipeline compiler that produces an execution plan;
- an execution engine that runs plans only;
- `ExecutionRun` as per-run state, not shared executor state;
- cancellation, retry, and timeout semantics; fallback provider resolution is now part of the runtime;
- global and capability middleware scopes;
- signals for lifecycle and execution events;
- worker contracts for execution, checkpoints, leases, and artifacts;
- deterministic configuration precedence.

## Frozen developer-experience guarantees

The repository must provide:

- `mirror startproject`;
- `mirror startapp`;
- `mirror doctor`;
- `mirror worker`;
- install-and-run smoke tests;
- a readable project scaffold;
- docs that explain the project without chat history.

## Frozen documentation guarantees

The repository must include:

- `README.md`;
- `CONTRIBUTING.md`;
- `CODE_OF_CONDUCT.md`;
- `ROADMAP.md`;
- `ALPHA_CHECKLIST.md`;
- `docs/ARCHITECTURE.md`;
- `docs/EXECUTION_SEMANTICS.md`;
- `docs/MIDDLEWARE_CONTRACT.md`;
- `docs/WORKER_CONTRACT.md`;
- `docs/SIGNAL_CONTRACT.md`;
- `docs/RELEASE_CHECKLIST.md`;
- `docs/FUTURE.md`;
- `docs/adr/README.md`;
- `docs/PRs/README.md`;
- concept docs;
- tutorial docs;
- reference docs;
- ADRs;
- PR notes.

## Deferred to beta

The following are intentionally deferred:

- distributed workers;
- dashboard and Django integration;
- REST and GraphQL interfaces;
- scheduling service;
- SaaS multi-tenancy;
- billing;
- Kubernetes orchestration;
- cluster scheduling.

## Non-negotiable review rule

If a behavior is promised, it must appear in:

1. code;
2. tests;
3. docs.

If any one of those is missing, the promise is incomplete.
