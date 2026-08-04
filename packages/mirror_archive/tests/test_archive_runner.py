"""Tests for archive runner."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchivePayload, ArchiveRequest, ArchiveResult
from mirror_archive.runner import archive_step


@pytest.mark.asyncio
async def test_archive_step_success():
    mock_provider = AsyncMock()
    resource_id = uuid4()
    request = ArchiveRequest(resource_id=resource_id, payload=ArchivePayload(content=b"test", target_uri="https://example.com"))
    expected = ArchiveResult(
        archive_id=uuid4(),
        path="/data/test.warc",
        size=1024,
        timestamp="2026-08-03T12:00:00Z",
    )
    mock_provider.archive.return_value = expected

    result = await archive_step(mock_provider, request)
    mock_provider.archive.assert_called_once_with(request)
    assert result == expected


@pytest.mark.asyncio
async def test_archive_step_raises_archive_error():
    mock_provider = AsyncMock()
    mock_provider.archive.side_effect = ArchiveError("provider error")
    request = ArchiveRequest(resource_id=uuid4(), payload=ArchivePayload(content=b"test", target_uri="https://example.com"))

    with pytest.raises(ArchiveError, match="provider error"):
        await archive_step(mock_provider, request)


@pytest.mark.asyncio
async def test_archive_step_wraps_unknown_error():
    mock_provider = AsyncMock()
    mock_provider.archive.side_effect = ValueError("unexpected")
    request = ArchiveRequest(resource_id=uuid4(), payload=ArchivePayload(content=b"test", target_uri="https://example.com"))

    with pytest.raises(ArchiveError) as exc:
        await archive_step(mock_provider, request)
    assert "unexpected" in str(exc.value)
