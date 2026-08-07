"""Capability descriptor for Embedding."""

from mirror_core.extensions.models import CapabilityManifest

from .models import EmbeddingRequest, EmbeddingResult
from .protocol import Embedder
from .settings import EmbeddingSettings

capability = CapabilityManifest(
    name="embedding",
    api_version="1.0.0",
    protocol=Embedder,
    request_model=EmbeddingRequest,
    result_model=EmbeddingResult,
    settings_model=EmbeddingSettings,
    runner="mirror_embedding.runner:embed_step",
    metadata={"summary": "Embedding capability"},
)
