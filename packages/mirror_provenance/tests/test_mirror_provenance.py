"""Tests for the Provenance capability."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from mirror_core.resource import ProducerRef, ResourceEnvelope
from mirror_provenance.capability import capability
from mirror_provenance.errors import ProvenanceError
from mirror_provenance.models import (
    ProvenanceInput,
    ProvenanceRequest,
    ProvenanceResult,
)
from mirror_provenance.runner import provenance_step
from mirror_provenance.settings import ProvenanceSettings
from pydantic import BaseModel


class Payload(BaseModel):
    """Simple payload used to validate provenance wrapping."""

    value: int


@pytest.mark.asyncio
async def test_provenance_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    producer = ProducerRef(capability="demo", capability_version="1.0", provider="memory")
    request = ProvenanceRequest(
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
    expected = ProvenanceResult(envelopes=[])
    provider.provenance.return_value = expected

    result = await provenance_step(provider, request)

    provider.provenance.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_provenance_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in ProvenanceError."""

    provider = AsyncMock()
    provider.provenance.side_effect = ValueError("boom")
    producer = ProducerRef(capability="demo", capability_version="1.0", provider="memory")
    request = ProvenanceRequest(
        envelopes=[
            ProvenanceInput(
                resource_type="Payload",
                schema_version="1.0",
                payload=Payload(value=1),
                producer=producer,
            )
        ]
    )

    with pytest.raises(ProvenanceError) as excinfo:
        await provenance_step(provider, request)

    assert "Failed to create provenance" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "provenance"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == ProvenanceRequest
    assert capability.result_model == ProvenanceResult
    assert capability.settings_model == ProvenanceSettings


def test_resource_envelope_creation() -> None:
    """The core resource envelope should remain immutable and fingerprinted."""

    producer = ProducerRef(capability="demo", capability_version="1.0", provider="memory")
    envelope = ResourceEnvelope.create(
        resource_type="Payload",
        schema_version="1.0",
        payload=Payload(value=1),
        producer=producer,
        parents=[uuid4()],
        metadata={"source": "test"},
    )
    assert envelope.payload == Payload(value=1)
    assert envelope.producer == producer
    assert envelope.metadata["source"] == "test"
