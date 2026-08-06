"""Tests for Archive capability descriptor."""

from mirror_archive.capability import capability
from mirror_archive.models import ArchiveRequest, ArchiveResult


def test_capability_descriptor():
    assert capability.name == "archive"
    assert capability.api_version == "1.0"
    assert capability.request_model == ArchiveRequest
    assert capability.result_model == ArchiveResult
    assert capability.runner == "mirror_archive.runner:archive_step"
