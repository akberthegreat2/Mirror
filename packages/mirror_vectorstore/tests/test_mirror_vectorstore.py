"""Tests for the Vector store capability."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_vectorstore.capability import capability
from mirror_vectorstore.models import (
    VectorQueryResult,
    VectorRecord,
    VectorStoreRequest,
    VectorStoreResult,
    VectorUpsertResult,
)
from mirror_vectorstore.runner import vectorstore_step
from mirror_vectorstore.settings import VectorStoreSettings
from pydantic import ValidationError


@pytest.mark.asyncio
async def test_vectorstore_step_dispatches_by_mode() -> None:
    """The runner should route upsert and query operations correctly."""

    provider = AsyncMock()
    provider.upsert.return_value = VectorUpsertResult(namespace="default", upserted=1)
    provider.query.return_value = VectorQueryResult(namespace="default", matches=[])

    upsert_request = VectorStoreRequest(
        mode="upsert",
        records=[VectorRecord(record_id="r1", vector=(1.0, 0.0), document_id="doc-1")],
    )
    query_request = VectorStoreRequest(mode="query", vector=[1.0, 0.0])

    upsert_result = await vectorstore_step(provider, upsert_request)
    query_result = await vectorstore_step(provider, query_request)

    assert upsert_result.upserted == 1
    assert query_result.matches == []
    provider.upsert.assert_called_once()
    provider.query.assert_called_once()


@pytest.mark.asyncio
async def test_vectorstore_step_wraps_unknown_error() -> None:
    """Unexpected provider failures should be wrapped in VectorStoreError."""

    provider = AsyncMock()
    provider.upsert.side_effect = ValueError("boom")
    request = VectorStoreRequest(
        mode="upsert",
        records=[VectorRecord(record_id="r1", vector=(1.0, 0.0), document_id="doc-1")],
    )

    with pytest.raises(Exception) as excinfo:
        await vectorstore_step(provider, request)

    assert "Failed to execute vector store operation" in str(excinfo.value)


def test_vectorstore_request_validation() -> None:
    """The request model should enforce mode-specific payloads."""

    with pytest.raises(ValidationError):
        VectorStoreRequest(mode="upsert")
    with pytest.raises(ValidationError):
        VectorStoreRequest(mode="query")


def test_capability_descriptor() -> None:
    """Capability descriptor should expose the public contract."""

    assert capability.name == "vectorstore"
    assert capability.api_version == "1.0.0"
    assert capability.request_model == VectorStoreRequest
    assert capability.result_model == VectorStoreResult
    assert capability.settings_model == VectorStoreSettings
