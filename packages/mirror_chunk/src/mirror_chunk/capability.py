"""Capability descriptor for Chunking."""

from mirror_core.extensions.models import CapabilityManifest

from .models import ChunkRequest, ChunkResult
from .protocol import Chunker
from .settings import ChunkSettings

capability = CapabilityManifest(
    name="chunk",
    api_version="1.0.0",
    protocol=Chunker,
    request_model=ChunkRequest,
    result_model=ChunkResult,
    settings_model=ChunkSettings,
    runner="mirror_chunk.runner:chunk_step",
    metadata={"summary": "Chunking capability"},
)
