"""Capability manifest for Provenance."""

from mirror_core.extensions.models import CapabilityManifest

from mirror_provenance.models import (
    ProvenanceInput,
    ProvenanceRequest,
    ProvenanceResult,
)
from mirror_provenance.protocol import Provenancer
from mirror_provenance.settings import ProvenanceSettings

capability = CapabilityManifest(
    name="provenance",
    api_version="1.0.0",
    protocol=Provenancer,
    request_model=ProvenanceRequest,
    result_model=ProvenanceResult,
    settings_model=ProvenanceSettings,
    runner="mirror_provenance.runner:provenance_step",
    input_ports={"envelopes": ProvenanceInput},
    metadata={"summary": "Deterministic provenance capability"},
)
