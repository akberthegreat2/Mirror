"""Tests for Fetch models."""

import pytest
from mirror_fetch.models import FetchRequest, FetchResult
from pydantic import ValidationError


def test_fetch_request_valid():
    req = FetchRequest(url="https://example.com")
    assert str(req.url) == "https://example.com/"
    assert req.method == "GET"
    assert req.timeout is None
    assert req.headers == {}


def test_fetch_request_invalid_method():
    with pytest.raises(ValidationError):
        FetchRequest(url="https://example.com", method="INVALID")


def test_fetch_result():
    result = FetchResult(
        url="https://example.com",
        status_code=200,
        content=b"<html></html>",
        encoding="utf-8",
        fetch_duration=0.5,
        timestamp="2026-08-03T12:00:00Z",
    )
    assert result.status_code == 200
    assert result.content == b"<html></html>"
