"""Tests for Fetch capability descriptor."""

from mirror_fetch.capability import capability
from mirror_fetch.models import FetchRequest, FetchResult


def test_capability_descriptor():
    assert capability.name == "fetch"
    assert capability.api_version == "1.0"
    assert capability.request_model == FetchRequest
    assert capability.result_model == FetchResult
    assert capability.runner == "mirror_fetch.runner:fetch_step"
