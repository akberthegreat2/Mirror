"""Mirror Retrieval capability – query vector stores for relevant passages."""

from mirror_retrieval.capability import capability
from mirror_retrieval.errors import RetrievalError
from mirror_retrieval.models import RetrievalHit, RetrievalRequest, RetrievalResult
from mirror_retrieval.protocol import Retriever
from mirror_retrieval.runner import retrieval_step
from mirror_retrieval.settings import RetrievalSettings

__all__ = [
    "RetrievalError",
    "RetrievalHit",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalSettings",
    "Retriever",
    "capability",
    "retrieval_step",
]
