"""Tests for the compliance provider."""

from __future__ import annotations

import pytest
from mirror_compliance.models import (
    ComplianceDocument,
    ComplianceRequest,
    ComplianceRule,
)
from mirror_compliance.settings import ComplianceSettings
from mirror_compliance_rules.provider import (
    RulesComplianceProvider,
    build_provider,
    provider,
)


@pytest.mark.asyncio
async def test_rules_compliance_provider_detects_violations() -> None:
    """Provider should flag forbidden terms and missing metadata."""

    provider_impl = RulesComplianceProvider()
    result = await provider_impl.check(
        ComplianceRequest(
            documents=[
                ComplianceDocument(
                    document_id="doc-1",
                    text="This document contains a secret password.",
                    metadata={},
                )
            ],
            rules=[
                ComplianceRule(
                    rule_id="no-secret",
                    forbidden_terms=("secret", "password"),
                    required_metadata_keys=("source",),
                    min_unique_words=3,
                )
            ],
        )
    )

    assessment = result.assessments[0]
    assert not assessment.compliant
    assert result.failed_count == 1
    assert assessment.findings[0].passed is False


def test_provider_descriptor() -> None:
    """Provider descriptor should expose the correct factory."""

    assert provider.name == "rules"
    assert provider.capability == "compliance"
    assert provider.factory == "mirror_compliance_rules.provider:build_provider"


def test_build_provider_uses_settings() -> None:
    """The provider factory should accept compliance settings."""

    built = build_provider(ComplianceSettings())
    assert isinstance(built, RulesComplianceProvider)
