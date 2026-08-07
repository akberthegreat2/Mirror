"""Tests for the enrichment provider."""

from __future__ import annotations

import pytest
from mirror_enrich.models import EnrichmentDocument, EnrichmentRequest
from mirror_enrich.settings import EnrichmentSettings
from mirror_enrich_text.provider import TextEnrichmentProvider, build_provider, provider


@pytest.mark.asyncio
async def test_text_enrichment_provider_extracts_signals() -> None:
    """Provider should derive stable metadata from text."""

    provider_impl = TextEnrichmentProvider()
    result = await provider_impl.enrich(
        EnrichmentRequest(
            documents=[
                EnrichmentDocument(
                    document_id="doc-1",
                    text="Mirror enriches text. Mirror enriches metadata. https://example.com",
                    metadata={"source": "test"},
                )
            ]
        )
    )

    enriched = result.documents[0]
    assert enriched.summary.startswith("Mirror enriches text.")
    assert "mirror" in enriched.keywords
    assert enriched.urls == ("https://example.com",)
    assert enriched.metadata["source"] == "test"
    assert enriched.metadata["enrichment"]["fingerprint"]


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "text"
    assert provider.capability == "enrich"
    assert provider.factory == "mirror_enrich_text.provider:build_provider"


def test_build_provider_uses_settings() -> None:
    """The provider factory should accept enrichment settings."""

    built = build_provider(EnrichmentSettings())
    assert isinstance(built, TextEnrichmentProvider)
