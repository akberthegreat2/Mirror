"""Deterministic text normalization provider."""

from __future__ import annotations

import re
import unicodedata

from mirror_core.extensions.models import ProviderManifest
from mirror_normalize.models import (
    NormalizationDocument,
    NormalizationRequest,
    NormalizationResult,
    NormalizedDocument,
)
from mirror_normalize.protocol import Normalizer
from mirror_normalize.settings import NormalizationSettings


class TextNormalizationProvider(Normalizer):
    """Canonicalize text using stable Unicode and whitespace rules."""

    def __init__(self, settings: NormalizationSettings | None = None) -> None:
        self._settings = settings or NormalizationSettings()

    async def normalize(self, request: NormalizationRequest) -> NormalizationResult:
        """Normalize a batch of documents."""

        documents = [self._normalize_document(document) for document in request.documents]
        return NormalizationResult(documents=documents)

    def _normalize_document(self, document: NormalizationDocument) -> NormalizedDocument:
        normalized = unicodedata.normalize(self._settings.unicode_form, document.text)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        if self._settings.lowercase:
            normalized = normalized.casefold()
        if self._settings.collapse_whitespace:
            normalized = re.sub(r"\s+", " ", normalized)
        if self._settings.strip_edges:
            normalized = normalized.strip()
        return NormalizedDocument(
            document_id=document.document_id,
            original_text=document.text,
            normalized_text=normalized,
            metadata=dict(document.metadata),
        )


provider = ProviderManifest(
    name="text",
    capability="normalize",
    capability_api="~=1.0",
    factory="mirror_normalize_text.provider:TextNormalizationProvider",
    settings_model="mirror_normalize.settings:NormalizationSettings",
    metadata={"description": "Deterministic text normalization provider."},
)
