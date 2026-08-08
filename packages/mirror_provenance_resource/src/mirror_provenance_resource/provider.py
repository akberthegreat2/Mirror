"""Deterministic provenance provider."""

from __future__ import annotations

from mirror_core.extensions.models import ProviderManifest
from mirror_core.resource import ResourceEnvelope
from mirror_provenance.models import ProvenanceRequest, ProvenanceResult
from mirror_provenance.protocol import Provenancer
from mirror_provenance.settings import ProvenanceSettings


class ResourceProvenanceProvider(Provenancer):
    """Wrap typed payloads in immutable provenance envelopes."""

    def __init__(self, settings: ProvenanceSettings | None = None) -> None:
        self._settings = settings or ProvenanceSettings()

    async def provenance(self, request: ProvenanceRequest) -> ProvenanceResult:
        """Create resource envelopes for one or more payloads."""

        envelopes = [
            ResourceEnvelope.create(
                resource_type=item.resource_type,
                schema_version=item.schema_version or self._settings.default_schema_version,
                payload=item.payload,
                producer=item.producer,
                parents=item.parents,
                metadata=item.metadata,
            )
            for item in request.envelopes
        ]
        return ProvenanceResult(envelopes=envelopes)


def build_provider(settings: ProvenanceSettings) -> ResourceProvenanceProvider:
    """Build a provenance provider from settings."""

    return ResourceProvenanceProvider(settings=settings)


provider = ProviderManifest(
    name="resource",
    capability="provenance",
    capability_api="~=1.0",
    factory="mirror_provenance_resource.provider:build_provider",
    settings_model="mirror_provenance.settings:ProvenanceSettings",
    metadata={"description": "Deterministic provenance provider."},
)
