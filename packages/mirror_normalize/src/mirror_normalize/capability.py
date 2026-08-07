"""Capability descriptor for Normalization."""

from mirror_core.extensions.models import CapabilityManifest

from .models import NormalizationRequest, NormalizationResult
from .protocol import Normalizer
from .settings import NormalizationSettings

capability = CapabilityManifest(
    name="normalize",
    api_version="1.0.0",
    protocol=Normalizer,
    request_model=NormalizationRequest,
    result_model=NormalizationResult,
    settings_model=NormalizationSettings,
    runner="mirror_normalize.runner:normalize_step",
    metadata={"summary": "Normalization capability"},
)
