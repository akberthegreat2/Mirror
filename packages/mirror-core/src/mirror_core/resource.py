"""Typed resource system with provenance and fingerprint.

Every capability consumes and produces typed resources. Resources are
wrapped in an envelope carrying provenance metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProducerRef(BaseModel):
    """Reference to the producer of a resource."""

    capability: str
    capability_version: str
    provider: str
    provider_version: str | None = None
    config_fingerprint: str | None = None
    step_id: str | None = None


class BlobReference(BaseModel):
    """Reference to a large payload stored externally."""

    uri: str
    checksum: str | None = None
    size: int | None = None
    media_type: str | None = None


class ResourceEnvelope(BaseModel):
    """Envelope wrapping a typed resource with provenance."""

    resource_id: UUID = Field(default_factory=uuid4)
    resource_type: str  # e.g., "FetchResult", "ArchiveResult"
    schema_version: str
    payload: BaseModel
    created_at: datetime = Field(default_factory=datetime.now)
    producer: ProducerRef
    parents: list[UUID] = Field(default_factory=list)
    fingerprint: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        resource_type: str,
        schema_version: str,
        payload: BaseModel,
        producer: ProducerRef,
        parents: list[UUID] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResourceEnvelope:
        """Create a new resource envelope with fingerprint."""
        import hashlib
        import json

        # Generate fingerprint from payload and metadata
        data = {
            "resource_type": resource_type,
            "schema_version": schema_version,
            "payload": payload.model_dump(mode="json"),
            "metadata": metadata or {},
        }
        fingerprint = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

        return cls(
            resource_type=resource_type,
            schema_version=schema_version,
            payload=payload,
            producer=producer,
            parents=parents or [],
            fingerprint=fingerprint,
            metadata=metadata or {},
        )