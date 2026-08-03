# ADR-0003: Single Resource Envelope with Provenance

## Status
Accepted

## Context
Different capabilities produce and consume different types of data (e.g., HTTP response, archive file path, extracted text). Without a common envelope, pipelines would pass raw dicts or custom objects, making type safety, provenance tracking, and serialization difficult.

## Decision
Every value passed between pipeline steps must be a `ResourceEnvelope`. This envelope contains:
- A typed payload (`BaseModel`).
- Metadata (producer, version, config fingerprint, timestamp).
- Lineage (parent resource IDs).
- A deterministic fingerprint for deduplication.
- An optional `BlobReference` for large payloads stored externally.

## Consequences
- All data exchange is typed and validated.
- Provenance is automatically tracked (who created what, from what).
- Serialization for distributed execution becomes straightforward.
- Deduplication is possible via fingerprint.
- Large payloads can be offloaded to storage without changing the pipeline.

## Alternatives Considered
- **Raw dicts**: No type safety; impossible to track provenance.
- **Custom objects per capability**: Would break the pipeline abstraction and require per-step parsing.
- **No envelope**: Data would be opaque; lineage lost.

## Decision Rationale
A single envelope with a typed payload provides a consistent, verifiable contract while enabling all needed metadata and storage capabilities.
