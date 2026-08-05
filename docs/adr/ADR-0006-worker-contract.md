# Worker contract

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror needs a contract for job execution before distributed workers are
added. The contract must exist even when the first implementation is local.

## Decision

The core SHALL define WorkerBackend, ExecutionStore, CheckpointStore,
ArtifactStore, and LeaseManager. The alpha implementation MAY be in-memory or
single-process. Distributed backends are deferred.

## Consequences

Later worker backends can plug into the same contract without rewriting the
application layer.
