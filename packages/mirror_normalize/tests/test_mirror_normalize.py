"""Tests for the Normalization capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_normalize.capability import capability
from mirror_normalize.errors import NormalizationError
from mirror_normalize.models import (
    NormalizationDocument,
    NormalizationRequest,
    NormalizationResult,
    NormalizedDocument,
)
from mirror_normalize.runner import normalize_step
from mirror_normalize.settings import NormalizationSettings
from pydantic import ValidationError


def test_normalization_models_validate_and_default() -> None:
    """Normalization models should validate and preserve metadata."""

    request = NormalizationRequest(
        documents=[
            NormalizationDocument(
                document_id="doc-1", text="  Hello  ", metadata={"source": "test"}
            )
        ]
    )
    assert request.documents[0].document_id == "doc-1"
    assert request.documents[0].metadata == {"source": "test"}

    result = NormalizationResult(
        documents=[
            NormalizedDocument(
                document_id="doc-1",
                original_text="  Hello  ",
                normalized_text="hello",
                metadata={"source": "test"},
            )
        ]
    )
    assert result.documents[0].normalized_text == "hello"

    with pytest.raises(ValidationError):
        NormalizationSettings(unicode_form="BAD")


@pytest.mark.asyncio
async def test_normalize_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = NormalizationRequest(
        documents=[NormalizationDocument(document_id="doc-1", text="Hello world")]
    )
    expected = NormalizationResult(
        documents=[
            NormalizedDocument(
                document_id="doc-1",
                original_text="Hello world",
                normalized_text="hello world",
            )
        ]
    )
    provider.normalize.return_value = expected

    result = await normalize_step(provider, request)

    provider.normalize.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_normalize_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in NormalizationError."""

    provider = AsyncMock()
    provider.normalize.side_effect = ValueError("boom")
    request = NormalizationRequest(
        documents=[NormalizationDocument(document_id="doc-1", text="Hello world")]
    )

    with pytest.raises(NormalizationError) as excinfo:
        await normalize_step(provider, request)

    assert "Failed to normalize" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "normalize"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == NormalizationRequest
    assert capability.result_model == NormalizationResult
    assert capability.settings_model == NormalizationSettings
