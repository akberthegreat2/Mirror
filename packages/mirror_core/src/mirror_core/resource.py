"""Typed resource system with provenance and fingerprint.

Every capability consumes and produces typed resources. Resources are
wrapped in an envelope carrying provenance metadata.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


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
    """Immutable envelope wrapping a typed resource with provenance."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    resource_id: UUID = Field(default_factory=uuid4)
    resource_type: str  # e.g., "FetchResult", "ArchiveResult"
    schema_version: str
    payload: BaseModel
    created_at: datetime = Field(default_factory=datetime.now)
    producer: ProducerRef
    parents: tuple[UUID, ...] = Field(default_factory=tuple)
    fingerprint: str
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any, /) -> None:
        object.__setattr__(self, "parents", tuple(self.parents))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @field_serializer("parents")
    def _serialize_parents(self, value: tuple[UUID, ...]) -> list[UUID]:
        return list(value)

    @field_serializer("metadata")
    def _serialize_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)

    @classmethod
    def create(
        cls,
        resource_type: str,
        schema_version: str,
        payload: BaseModel,
        producer: ProducerRef,
        parents: list[UUID] | tuple[UUID, ...] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ResourceEnvelope:
        """Create a new resource envelope with fingerprint."""
        import hashlib
        import json

        # Generate fingerprint from payload and metadata
        normalized_metadata = dict(metadata or {})
        data = {
            "resource_type": resource_type,
            "schema_version": schema_version,
            "payload": payload.model_dump(mode="json"),
            "metadata": normalized_metadata,
        }
        fingerprint = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

        return cls(
            resource_type=resource_type,
            schema_version=schema_version,
            payload=payload,
            producer=producer,
            parents=tuple(parents or ()),
            fingerprint=fingerprint,
            metadata=normalized_metadata,
        )
