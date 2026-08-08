"""Deterministic retrieval provider composed from configured embedding and vector store contracts."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from mirror_core.extensions.models import ProviderManifest
from mirror_embedding.models import EmbeddingInput, EmbeddingRequest
from mirror_embedding.protocol import Embedder
from mirror_embedding.settings import EmbeddingSettings
from mirror_retrieval.models import RetrievalHit, RetrievalRequest, RetrievalResult
from mirror_retrieval.protocol import Retriever
from mirror_retrieval.settings import RetrievalSettings
from mirror_vectorstore.models import VectorQueryRequest
from mirror_vectorstore.protocol import VectorStore
from mirror_vectorstore.settings import VectorStoreSettings
from pydantic import BaseModel


class MemoryRetrievalProvider(Retriever):
    """Resolve retrieval queries with a deterministic in-memory index."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        settings: RetrievalSettings | None = None,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._settings = settings or RetrievalSettings()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Return the nearest records for a textual query."""

        namespace = request.namespace or self._settings.default_namespace
        top_k = request.top_k or self._settings.default_top_k
        embedding = await self._embedder.embed(
            EmbeddingRequest(
                items=[EmbeddingInput(item_id="query", text=request.query)]
            )
        )
        vector = list(embedding.vectors[0].values)
        query_result = await self._vector_store.query(
            VectorQueryRequest(
                namespace=namespace,
                vector=vector,
                top_k=top_k,
                filters=request.filters,
            )
        )
        matches = [
            RetrievalHit(
                record_id=match.record.record_id,
                document_id=match.record.document_id,
                chunk_id=match.record.chunk_id,
                score=match.score,
                text=match.record.text,
                metadata=dict(match.record.metadata),
                provenance={
                    "record_id": match.record.record_id,
                    "document_id": match.record.document_id,
                    "chunk_id": match.record.chunk_id,
                    **dict(
                        match.record.metadata.get("provenance", match.record.metadata)
                    ),
                },
                score_details={"similarity": match.score},
            )
            for match in query_result.matches
        ]
        evaluation = {
            "top_k": top_k,
            "namespace": namespace,
            "embedding_factory": self._settings.embedder_factory,
            "vector_store_factory": self._settings.vector_store_factory,
        }
        return RetrievalResult(
            query=request.query,
            namespace=namespace,
            matches=matches,
            evaluation=evaluation,
        )


def _load_symbol(path: str) -> Any:
    """Load a callable or class from a ``module:attribute`` path."""

    module_path, separator, name = path.rpartition(":")
    if not separator:
        raise ValueError(f"Invalid factory path: {path!r}")
    return getattr(importlib.import_module(module_path), name)


def _instantiate(factory: Any, settings: BaseModel | None = None) -> Any:
    """Instantiate a factory with an optional settings model."""

    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return factory() if settings is None else factory(settings)

    accepts_settings = "settings" in signature.parameters
    accepts_var_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    if settings is None:
        return factory()
    if accepts_settings or accepts_var_kwargs:
        return factory(settings=settings)
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
    ]
    if positional:
        return factory(settings)
    raise TypeError(f"Factory {factory!r} does not accept a settings object")


def _build_dependency(factory_path: str, settings: BaseModel) -> Any:
    """Build a provider dependency from its configured factory path."""

    factory = _load_symbol(factory_path)
    return _instantiate(factory, settings=settings)


def build_provider(settings: RetrievalSettings) -> MemoryRetrievalProvider:
    """Build a retrieval provider from configured first-party dependencies."""

    embedder_settings = EmbeddingSettings.model_validate(settings.embedder_settings)
    vector_store_settings = VectorStoreSettings.model_validate(
        settings.vector_store_settings
    )
    return MemoryRetrievalProvider(
        embedder=_build_dependency(settings.embedder_factory, embedder_settings),
        vector_store=_build_dependency(
            settings.vector_store_factory, vector_store_settings
        ),
        settings=settings,
    )


provider = ProviderManifest(
    name="memory",
    capability="retrieval",
    capability_api="~=1.0",
    factory="mirror_retrieval_memory.provider:build_provider",
    settings_model="mirror_retrieval.settings:RetrievalSettings",
    metadata={"description": "Deterministic in-memory retrieval provider."},
)
