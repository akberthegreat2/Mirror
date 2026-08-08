"""Settings for the Retrieval capability."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RetrievalSettings(BaseModel):
    """Runtime defaults and dependency factories for retrieval."""

    default_top_k: int = Field(default=5, ge=1, le=100)
    default_namespace: str = Field(default="default", min_length=1)
    embedder_factory: str = Field(
        default="mirror_embedding_hash.provider:HashEmbeddingProvider"
    )
    embedder_settings: dict[str, Any] = Field(default_factory=dict)
    vector_store_factory: str = Field(
        default="mirror_vectorstore_memory.provider:MemoryVectorStoreProvider"
    )
    vector_store_settings: dict[str, Any] = Field(default_factory=dict)
