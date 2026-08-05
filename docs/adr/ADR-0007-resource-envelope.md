# Resource envelope

**Status:** Accepted  
**Date:** 2026-08-05

## Context

Mirror passes typed resources between steps. Those resources need stable
identity and provenance so that results can be traced later.

## Decision

ResourceEnvelope, ProducerRef, and BlobReference MUST be immutable models.
Each envelope MUST carry the producer, parent references, and a stable
fingerprint. Large payloads SHOULD move through blob references instead of
inline copying.

## Consequences

The framework keeps lineage honest and becomes ready for durable execution
later.
