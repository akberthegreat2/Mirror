# PR: Core alpha runtime foundation

## Problem

The workspace had a healthy package split, but a few runtime and packaging edges still blocked a usable alpha:

- middleware entry points exported functions/dicts instead of immutable manifests;
- middleware invocations were untyped dictionaries;
- WARC imports failed eagerly when warcio was unavailable;
- CLI helper commands leaked event loops and application resources;
- the workspace had a few packaging rough edges and missing package READMEs.

## What changed

### Core runtime

- Added a typed MiddlewareInvocation model to mirror_core.middleware.
- Updated the middleware protocol and chain executor to consume typed invocations.
- Updated the executor to pass MiddlewareInvocation objects instead of dictionaries.
- Added a safe AST-based condition evaluator; it no longer uses eval().
- Kept ExecutionRun isolated per execution and preserved concurrent run safety.

### Middleware package

- Replaced callable/dict middleware entry points with immutable MiddlewareManifest manifests.
- Updated retry, timeout, ratelimit, logging, and tracing to use typed invocations.
- Added manifest objects for entry-point discovery.
- Kept compatibility helpers that return the manifest objects.
- Fixed rate limiting to avoid sleeping while holding the lock.
- Fixed logging to read Step models instead of dictionary keys.
- Added lightweight trace context propagation.

### Application and lifecycle

- Built middleware chains from selected settings using the registry and manifest ordering.
- Added capability-aware middleware chain selection.
- Kept transactional startup and restartable shutdown behavior.

### CLI and packaging

- Reworked CLI listing commands to use asyncio.run() and async with Application(...).
- Added the missing rich dependency for the CLI package.
- Added package READMEs for the packages that were missing them.
- Fixed the archive package dependency typo (mirro_core → mirror-core).
- Normalized package metadata and bootstrap files.

## Follow-ups

- Continue improving contract coverage around middleware construction.
