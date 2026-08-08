"""Tests for the provenance provider."""

from __future__ import annotations

from uuid import uuid4

import pytest
from mirror_core.resource import ProducerRef
from mirror_provenance.models import ProvenanceInput, ProvenanceRequest
from mirror_provenance.settings import ProvenanceSettings
from mirror_provenance_resource.provider import (
    ResourceProvenanceProvider,
    build_provider,
    provider,
)
from pydantic import BaseModel


class Payload(BaseModel):
    """Simple payload used to validate provenance creation."""

    value: int


@pytest.mark.asyncio
async def test_resource_provenance_provider_creates_envelopes() -> None:
    """Provider should create immutable resource envelopes."""

    provider_impl = ResourceProvenanceProvider()
    producer = ProducerRef(capability="demo", capability_version="1.0", provider="resource")
    result = await provider_impl.provenance(
        ProvenanceRequest(
            envelopes=[
                ProvenanceInput(
                    resource_type="Payload",
                    schema_version="1.0",
                    payload=Payload(value=1),
                    producer=producer,
                    parents=[uuid4()],
                    metadata={"source": "test"},
                )
            ]
        )
    )

    envelope = result.envelopes[0]
    assert envelope.payload == Payload(value=1)
    assert envelope.producer == producer
    assert envelope.metadata["source"] == "test"


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "resource"
    assert provider.capability == "provenance"
    assert provider.factory == "mirror_provenance_resource.provider:build_provider"


def test_build_provider_uses_settings() -> None:
    """The provider factory should accept provenance settings."""

    built = build_provider(ProvenanceSettings())
    assert isinstance(built, ResourceProvenanceProvider)
