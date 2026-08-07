"""Capability manifest for Deduplication."""

from mirror_core.extensions.models import CapabilityManifest

from mirror_dedup.models import DedupRequest, DedupResult
from mirror_dedup.protocol import Deduplicator
from mirror_dedup.settings import DedupSettings

capability = CapabilityManifest(
    name="dedup",
    api_version="1.0.0",
    protocol=Deduplicator,
    request_model=DedupRequest,
    result_model=DedupResult,
    settings_model=DedupSettings,
    runner="mirror_dedup.runner:dedup_step",
    metadata={"summary": "Deterministic document deduplication capability"},
)
