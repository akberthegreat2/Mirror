"""Typed models for the Provenance capability."""

from __future__ import annotations

from uuid import UUID

from mirror_core.resource import ProducerRef, ResourceEnvelope
from pydantic import BaseModel, ConfigDict, Field


class ProvenanceInput(BaseModel):
    """A typed payload ready to be wrapped in a resource envelope."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    resource_type: str
    schema_version: str
    payload: BaseModel
    producer: ProducerRef
    parents: list[UUID] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class ProvenanceRequest(BaseModel):
    """Input for a provenance run."""

    envelopes: list[ProvenanceInput] = Field(default_factory=list)


class ProvenanceResult(BaseModel):
    """Output of a provenance run."""

    envelopes: list[ResourceEnvelope] = Field(default_factory=list)
