"""Tests for the Embedding capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_embedding.capability import capability
from mirror_embedding.errors import EmbeddingError
from mirror_embedding.models import (
    EmbeddingInput,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingVector,
)
from mirror_embedding.runner import embed_step
from mirror_embedding.settings import EmbeddingSettings
from pydantic import ValidationError


def test_embedding_settings_validate_dimension() -> None:
    """Embedding settings should reject odd dimensions."""

    with pytest.raises(ValidationError):
        EmbeddingSettings(dimension=63)


@pytest.mark.asyncio
async def test_embed_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = EmbeddingRequest(items=[EmbeddingInput(item_id="item-1", text="hello world")])
    expected = EmbeddingResult(vectors=[EmbeddingVector(item_id="item-1", values=(1.0, 0.0))])
    provider.embed.return_value = expected

    result = await embed_step(provider, request)

    provider.embed.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_embed_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in EmbeddingError."""

    provider = AsyncMock()
    provider.embed.side_effect = ValueError("boom")
    request = EmbeddingRequest(items=[EmbeddingInput(item_id="item-1", text="hello world")])

    with pytest.raises(EmbeddingError) as excinfo:
        await embed_step(provider, request)

    assert "Failed to embed" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "embedding"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == EmbeddingRequest
    assert capability.result_model == EmbeddingResult
    assert capability.settings_model == EmbeddingSettings
