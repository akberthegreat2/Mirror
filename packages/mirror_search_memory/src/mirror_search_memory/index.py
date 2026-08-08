"""Search index implementations for the in-memory provider."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from mirror_search.models import SearchHit


class MemorySearchIndex:
    """A tiny search index with a familiar OpenSearch-like shape."""

    def __init__(self) -> None:
        self._documents: dict[str, dict[str, Any]] = {}
        self._inverted: dict[str, set[str]] = defaultdict(set)

    def add(
        self,
        document_id: str,
        *,
        text: str,
        title: str | None = None,
        url: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        record = {
            "document_id": document_id,
            "text": text,
            "title": title,
            "url": url,
            "metadata": dict(metadata or {}),
        }
        self._documents[document_id] = record
        for token in set(_tokenize(text) + _tokenize(title or "") + _tokenize(url or "")):
            self._inverted[token].add(document_id)

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        query_tokens = _tokenize(query)
        scores: Counter[str] = Counter()
        for token in query_tokens:
            for document_id in self._inverted.get(token, set()):
                scores[document_id] += 1
        hits: list[SearchHit] = []
        for document_id, score in scores.most_common(limit):
            record = self._documents[document_id]
            snippet = _snippet(record["text"], query_tokens)
            hits.append(
                SearchHit(
                    document_id=document_id,
                    score=float(score),
                    title=record.get("title"),
                    url=record.get("url"),
                    snippet=snippet,
                )
            )
        return hits


class OpenSearchIndex:
    """Optional OpenSearch adapter for enterprise deployments."""

    def __init__(self, *, hosts: Sequence[str], index_name: str = "mirror-documents") -> None:
        try:
            from opensearchpy import OpenSearch  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise ImportError("opensearchpy is not installed; install the 'opensearch-py' package to use OpenSearchIndex") from exc
        self._client = OpenSearch(hosts=list(hosts))
        self._index_name = index_name

    def add(
        self,
        document_id: str,
        *,
        text: str,
        title: str | None = None,
        url: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        body = {
            "text": text,
            "title": title,
            "url": url,
            "metadata": dict(metadata or {}),
        }
        self._client.index(index=self._index_name, id=document_id, body=body, refresh=True)

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        response = self._client.search(
            index=self._index_name,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "text", "url"],
                    }
                }
            },
            size=limit,
        )
        hits: list[SearchHit] = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            hits.append(
                SearchHit(
                    document_id=str(hit.get("_id")),
                    score=float(hit.get("_score", 0.0)),
                    title=source.get("title"),
                    url=source.get("url"),
                    snippet=_snippet(source.get("text", ""), _tokenize(query)),
                )
            )
        return hits


def _tokenize(text: str) -> list[str]:
    import re

    return [token.lower() for token in re.findall(r"[A-Za-z0-9']+", text)]


def _snippet(text: str, tokens: Sequence[str], *, width: int = 24) -> str | None:
    if not text or not tokens:
        return text[:120] if text else None
    lowered = text.lower()
    best_index = min((lowered.find(token) for token in tokens if token in lowered), default=-1)
    if best_index < 0:
        return text[:120]
    start = max(0, best_index - 40)
    end = min(len(text), best_index + width)
    return " ".join(text[start:end].split())
