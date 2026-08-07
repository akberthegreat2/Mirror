"""Deterministic document deduplication provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from mirror_core.extensions.models import ProviderManifest
from mirror_dedup.models import (
    DedupDecision,
    DedupDocument,
    DeduplicatedDocument,
    DedupRequest,
    DedupResult,
)
from mirror_dedup.protocol import Deduplicator
from mirror_dedup.settings import DedupSettings


class HashDedupProvider(Deduplicator):
    """Canonicalize documents and remove duplicates by fingerprint."""

    def __init__(self, settings: DedupSettings | None = None) -> None:
        self._settings = settings or DedupSettings()

    async def dedup(self, request: DedupRequest) -> DedupResult:
        """Deduplicate a batch of text documents."""

        canonical_documents: dict[str, DeduplicatedDocument] = {}
        duplicate_counts: dict[str, int] = {}
        duplicates: list[DedupDecision] = []

        for document in request.documents:
            fingerprint = self._fingerprint(document)
            existing = canonical_documents.get(fingerprint)
            if existing is None:
                canonical_documents[fingerprint] = DeduplicatedDocument(
                    document_id=document.document_id,
                    text=self._canonical_text(document.text),
                    fingerprint=fingerprint,
                    duplicate_count=0,
                    metadata=self._retained_metadata(document, fingerprint, 0),
                )
                duplicate_counts[fingerprint] = 0
                continue

            duplicate_counts[fingerprint] += 1
            duplicates.append(
                DedupDecision(
                    duplicate_document_id=document.document_id,
                    canonical_document_id=existing.document_id,
                    fingerprint=fingerprint,
                )
            )
            canonical_documents[fingerprint] = DeduplicatedDocument(
                document_id=existing.document_id,
                text=existing.text,
                fingerprint=fingerprint,
                duplicate_count=duplicate_counts[fingerprint],
                metadata=self._retained_metadata(
                    DedupDocument(
                        document_id=existing.document_id,
                        text=existing.text,
                        metadata=existing.metadata,
                    ),
                    fingerprint,
                    duplicate_counts[fingerprint],
                ),
            )

        documents = list(canonical_documents.values())
        return DedupResult(
            documents=documents,
            duplicates=duplicates,
            removed_count=len(duplicates),
        )

    def _canonical_text(self, text: str) -> str:
        """Normalize text before hashing."""

        normalized = unicodedata.normalize(self._settings.unicode_form, text)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        if self._settings.collapse_whitespace:
            normalized = re.sub(r"\s+", " ", normalized)
        if self._settings.casefold:
            normalized = normalized.casefold()
        return normalized.strip()

    def _fingerprint_metadata(self, document: DedupDocument) -> dict[str, object]:
        """Extract the metadata fields that contribute to deduplication."""

        metadata: dict[str, object] = {}
        for key in self._settings.fingerprint_metadata_keys:
            if key in document.metadata:
                metadata[key] = document.metadata[key]
        return metadata

    def _retained_metadata(
        self,
        document: DedupDocument,
        fingerprint: str,
        duplicate_count: int,
    ) -> dict[str, object]:
        """Return retained metadata for a canonical document."""

        metadata = dict(document.metadata)
        metadata["dedup"] = {
            "fingerprint": fingerprint,
            "duplicate_count": duplicate_count,
        }
        return metadata

    def _fingerprint(self, document: DedupDocument) -> str:
        """Compute a stable fingerprint for one document."""

        payload = {
            "text": self._canonical_text(document.text),
            "metadata": self._fingerprint_metadata(document),
        }
        digest = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
        return digest


def build_provider(settings: DedupSettings) -> HashDedupProvider:
    """Build a hash deduplication provider from settings."""

    return HashDedupProvider(settings=settings)


provider = ProviderManifest(
    name="hash",
    capability="dedup",
    capability_api="~=1.0",
    factory="mirror_dedup_hash.provider:build_provider",
    settings_model="mirror_dedup.settings:DedupSettings",
    metadata={"description": "Deterministic hash deduplication provider."},
)
