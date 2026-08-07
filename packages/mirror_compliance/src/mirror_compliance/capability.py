"""Capability manifest for Compliance."""

from mirror_core.extensions.models import CapabilityManifest

from mirror_compliance.models import ComplianceRequest, ComplianceResult
from mirror_compliance.protocol import ComplianceChecker
from mirror_compliance.settings import ComplianceSettings

capability = CapabilityManifest(
    name="compliance",
    api_version="1.0.0",
    protocol=ComplianceChecker,
    request_model=ComplianceRequest,
    result_model=ComplianceResult,
    settings_model=ComplianceSettings,
    runner="mirror_compliance.runner:compliance_step",
    metadata={"summary": "Deterministic policy and compliance capability"},
)
