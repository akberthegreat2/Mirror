"""Capability descriptor for Vector storage."""

from mirror_core.extensions.models import CapabilityManifest

from .models import VectorStoreRequest, VectorStoreResult
from .protocol import VectorStore
from .settings import VectorStoreSettings

capability = CapabilityManifest(
    name="vectorstore",
    api_version="1.0.0",
    protocol=VectorStore,
    request_model=VectorStoreRequest,
    result_model=VectorStoreResult,
    settings_model=VectorStoreSettings,
    runner="mirror_vectorstore.runner:vectorstore_step",
    metadata={"summary": "Vector store capability"},
)
