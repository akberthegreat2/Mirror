"""Capability descriptor for Retrieval."""

from mirror_core.extensions.models import CapabilityManifest

from .models import RetrievalRequest, RetrievalResult
from .protocol import Retriever
from .settings import RetrievalSettings

capability = CapabilityManifest(
    name="retrieval",
    api_version="1.0.0",
    protocol=Retriever,
    request_model=RetrievalRequest,
    result_model=RetrievalResult,
    settings_model=RetrievalSettings,
    runner="mirror_retrieval.runner:retrieval_step",
    metadata={"summary": "Retrieval capability"},
)
