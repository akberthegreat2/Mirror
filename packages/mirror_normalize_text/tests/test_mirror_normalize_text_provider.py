"""Tests for the normalization provider."""

from __future__ import annotations

import pytest
from mirror_normalize.models import NormalizationDocument, NormalizationRequest
from mirror_normalize.settings import NormalizationSettings
from mirror_normalize_text.provider import TextNormalizationProvider, provider


@pytest.mark.asyncio
async def test_text_normalization_provider_normalizes_text() -> None:
    """Provider should lowercase, collapse whitespace, and preserve metadata."""

    provider_impl = TextNormalizationProvider(NormalizationSettings())
    request = NormalizationRequest(
        documents=[
            NormalizationDocument(
                document_id="doc-1",
                text="  Hello\n\nWORLD  ",
                metadata={"source": "test"},
            )
        ]
    )

    result = await provider_impl.normalize(request)

    assert result.documents[0].normalized_text == "hello world"
    assert result.documents[0].metadata == {"source": "test"}


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "text"
    assert provider.capability == "normalize"
    assert provider.factory == "mirror_normalize_text.provider:TextNormalizationProvider"
