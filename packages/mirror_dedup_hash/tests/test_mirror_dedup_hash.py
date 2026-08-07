"""Tests for the deduplication provider."""

from __future__ import annotations

import pytest
from mirror_dedup.models import DedupDocument, DedupRequest
from mirror_dedup.settings import DedupSettings
from mirror_dedup_hash.provider import HashDedupProvider, build_provider, provider


@pytest.mark.asyncio
async def test_hash_dedup_provider_removes_duplicates() -> None:
    """Provider should keep one canonical document per fingerprint."""

    provider_impl = HashDedupProvider()
    result = await provider_impl.dedup(
        DedupRequest(
            documents=[
                DedupDocument(
                    document_id="doc-1",
                    text="Mirror is clean.",
                    metadata={"source": "one"},
                ),
                DedupDocument(
                    document_id="doc-2",
                    text="Mirror is clean.",
                    metadata={"source": "two"},
                ),
            ]
        )
    )

    assert len(result.documents) == 1
    assert result.removed_count == 1
    assert result.duplicates[0].duplicate_document_id == "doc-2"
    assert result.documents[0].duplicate_count == 1


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "hash"
    assert provider.capability == "dedup"
    assert provider.factory == "mirror_dedup_hash.provider:build_provider"


def test_build_provider_uses_settings() -> None:
    """The provider factory should accept dedup settings."""

    built = build_provider(DedupSettings())
    assert isinstance(built, HashDedupProvider)
