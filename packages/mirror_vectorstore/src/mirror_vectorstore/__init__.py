"""Mirror Vector store capability – persist and query embeddings."""

from mirror_vectorstore.capability import capability
from mirror_vectorstore.errors import VectorStoreError
from mirror_vectorstore.models import (
    VectorMatch,
    VectorQueryRequest,
    VectorQueryResult,
    VectorRecord,
    VectorStoreRequest,
    VectorStoreResult,
    VectorUpsertRequest,
    VectorUpsertResult,
)
from mirror_vectorstore.protocol import VectorStore
from mirror_vectorstore.runner import vectorstore_step
from mirror_vectorstore.settings import VectorStoreSettings

__all__ = [
    "VectorMatch",
    "VectorQueryRequest",
    "VectorQueryResult",
    "VectorRecord",
    "VectorStore",
    "VectorStoreError",
    "VectorStoreRequest",
    "VectorStoreResult",
    "VectorStoreSettings",
    "VectorUpsertRequest",
    "VectorUpsertResult",
    "capability",
    "vectorstore_step",
]
