"""Deterministic text enrichment provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter

from mirror_core.extensions.models import ProviderManifest
from mirror_enrich.models import (
    EnrichedDocument,
    EnrichmentDocument,
    EnrichmentRequest,
    EnrichmentResult,
    EnrichmentStatistics,
)
from mirror_enrich.protocol import Enricher
from mirror_enrich.settings import EnrichmentSettings

TOKEN_RE = re.compile(r"[A-Za-z0-9']+")
URL_RE = re.compile(r"https?://\S+|www\.\S+")


class TextEnrichmentProvider(Enricher):
    """Canonicalize text into deterministic summary and keyword signals."""

    def __init__(self, settings: EnrichmentSettings | None = None) -> None:
        self._settings = settings or EnrichmentSettings()

    async def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        """Enrich a batch of documents with stable derived metadata."""

        documents = [self._enrich_document(document) for document in request.documents]
        return EnrichmentResult(documents=documents)

    def _enrich_document(self, document: EnrichmentDocument) -> EnrichedDocument:
        text = unicodedata.normalize(self._settings.unicode_form, document.text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if self._settings.collapse_whitespace:
            text = re.sub(r"\s+", " ", text)
        if self._settings.strip_edges:
            text = text.strip()

        tokens = [token.casefold() for token in TOKEN_RE.findall(text)]
        filtered = [
            token
            for token in tokens
            if len(token) >= self._settings.min_keyword_length
            and token not in self._settings.stopwords
        ]
        counts = Counter(filtered)
        keywords = tuple(
            token
            for token, _ in sorted(
                counts.items(), key=lambda item: (-item[1], item[0])
            )[: self._settings.max_keywords]
        )
        urls = tuple(dict.fromkeys(URL_RE.findall(document.text)))
        summary_words = text.split()[: self._settings.summary_word_limit]
        summary = " ".join(summary_words)
        statistics = EnrichmentStatistics(
            character_count=len(text),
            line_count=max(text.count("\n") + 1, 1),
            sentence_count=max(len(re.findall(r"[.!?]+", text)), 1 if text else 0),
            word_count=len(tokens),
            unique_word_count=len(set(tokens)),
            keyword_count=len(keywords),
            url_count=len(urls),
        )
        metadata = dict(document.metadata)
        metadata["enrichment"] = {
            "fingerprint": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "keywords": keywords,
            "urls": urls,
            "summary": summary,
        }
        return EnrichedDocument(
            document_id=document.document_id,
            original_text=document.text,
            enriched_text=text,
            summary=summary,
            keywords=keywords,
            urls=urls,
            statistics=statistics,
            metadata=metadata,
        )


def build_provider(settings: EnrichmentSettings) -> TextEnrichmentProvider:
    """Build a text enrichment provider from settings."""

    return TextEnrichmentProvider(settings=settings)


provider = ProviderManifest(
    name="text",
    capability="enrich",
    capability_api="~=1.0",
    factory="mirror_enrich_text.provider:build_provider",
    settings_model="mirror_enrich.settings:EnrichmentSettings",
    metadata={"description": "Deterministic text enrichment provider."},
)
