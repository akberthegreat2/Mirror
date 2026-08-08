"""Tests for the Compliance capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_compliance.capability import capability
from mirror_compliance.errors import ComplianceError
from mirror_compliance.models import (
    ComplianceAssessment,
    ComplianceDocument,
    ComplianceRequest,
    ComplianceResult,
)
from mirror_compliance.runner import compliance_step
from mirror_compliance.settings import ComplianceSettings


@pytest.mark.asyncio
async def test_compliance_step_success() -> None:
    """The runner should delegate to the provider."""

    provider = AsyncMock()
    request = ComplianceRequest(documents=[ComplianceDocument(document_id="doc-1", text="Mirror", metadata={"source": "test"})])
    expected = ComplianceResult(
        assessments=[
            ComplianceAssessment(
                document_id="doc-1",
                compliant=True,
                findings=[],
            )
        ],
        compliant=True,
        passed_count=1,
        failed_count=0,
    )
    provider.check.return_value = expected

    result = await compliance_step(provider, request)

    provider.check.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_compliance_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in ComplianceError."""

    provider = AsyncMock()
    provider.check.side_effect = ValueError("boom")
    request = ComplianceRequest(documents=[ComplianceDocument(document_id="doc-1", text="Mirror", metadata={"source": "test"})])

    with pytest.raises(ComplianceError) as excinfo:
        await compliance_step(provider, request)

    assert "Failed to evaluate compliance" in str(excinfo.value)


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "compliance"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == ComplianceRequest
    assert capability.result_model == ComplianceResult
    assert capability.settings_model == ComplianceSettings
