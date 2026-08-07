"""Capability descriptor for Enrichment."""

from mirror_core.extensions.models import CapabilityManifest

from mirror_enrich.models import EnrichmentRequest, EnrichmentResult
from mirror_enrich.protocol import Enricher
from mirror_enrich.settings import EnrichmentSettings

capability = CapabilityManifest(
    name="enrich",
    api_version="1.0.0",
    protocol=Enricher,
    request_model=EnrichmentRequest,
    result_model=EnrichmentResult,
    settings_model=EnrichmentSettings,
    runner="mirror_enrich.runner:enrich_step",
    metadata={"summary": "Deterministic text enrichment capability"},
)
