"""Tests for Archive models."""

from uuid import uuid4

from mirror_archive.models import ArchiveRequest, ArchiveResult


def test_archive_request():
    req = ArchiveRequest(resource_id=uuid4(), payload={"data": "test"})
    assert req.resource_id is not None
    assert req.payload == {"data": "test"}


def test_archive_result():
    result = ArchiveResult(
        archive_id=uuid4(),
        path="/data/archive/test.warc",
        size=1024,
        checksum="sha256:abc123",
        timestamp="2026-08-03T12:00:00Z",
    )
    assert result.size == 1024
