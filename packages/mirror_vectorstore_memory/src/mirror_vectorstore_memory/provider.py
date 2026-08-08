"""In-memory vector store provider."""

from __future__ import annotations

import math

from mirror_core.extensions.models import ProviderManifest
from mirror_vectorstore.models import (
    VectorMatch,
    VectorQueryRequest,
    VectorQueryResult,
    VectorRecord,
    VectorUpsertRequest,
    VectorUpsertResult,
)
from mirror_vectorstore.protocol import VectorStore
from mirror_vectorstore.settings import VectorStoreSettings


class MemoryVectorStoreProvider(VectorStore):
    """Store vectors in memory and query them with cosine similarity."""

    def __init__(self, settings: VectorStoreSettings | None = None) -> None:
        self._settings = settings or VectorStoreSettings()
        self._namespaces: dict[str, dict[str, VectorRecord]] = {}

    async def upsert(self, request: VectorUpsertRequest) -> VectorUpsertResult:
        """Store or replace records in a namespace."""

        bucket = self._namespaces.setdefault(request.namespace, {})
        for record in request.records:
            self._validate_record(record)
            bucket[record.record_id] = record
        return VectorUpsertResult(namespace=request.namespace, upserted=len(request.records))

    async def query(self, request: VectorQueryRequest) -> VectorQueryResult:
        """Return the nearest records for a query vector."""

        bucket = self._namespaces.get(request.namespace, {})
        if not bucket:
            return VectorQueryResult(namespace=request.namespace, matches=[])

        query_vector = tuple(request.vector)
        matches = [
            VectorMatch(
                record=record,
                score=self._cosine_similarity(query_vector, record.vector),
            )
            for record in bucket.values()
            if self._matches_filters(record, request.filters)
        ]
        matches.sort(key=lambda match: (-match.score, match.record.record_id))
        return VectorQueryResult(namespace=request.namespace, matches=matches[: request.top_k])

    def _validate_record(self, record: VectorRecord) -> None:
        if not record.vector:
            raise ValueError(f"record '{record.record_id}' must include a vector")

    def _matches_filters(self, record: VectorRecord, filters: dict[str, object]) -> bool:
        for key, expected in filters.items():
            actual = record.metadata.get(key)
            if actual != expected:
                return False
        return True

    def _cosine_similarity(self, left: tuple[float, ...], right: tuple[float, ...]) -> float:
        if not left or not right:
            return 0.0
        length = min(len(left), len(right))
        dot = sum(left[i] * right[i] for i in range(length))
        left_norm = math.sqrt(sum(value * value for value in left[:length]))
        right_norm = math.sqrt(sum(value * value for value in right[:length]))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)


provider = ProviderManifest(
    name="memory",
    capability="vectorstore",
    capability_api="~=1.0",
    factory="mirror_vectorstore_memory.provider:MemoryVectorStoreProvider",
    settings_model="mirror_vectorstore.settings:VectorStoreSettings",
    metadata={"description": "In-memory vector store provider."},
)
