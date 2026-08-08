"""REST API smoke tests for the Mirror control plane."""

from __future__ import annotations

from django.urls import reverse
from rest_framework.test import APIClient


def test_manifest_endpoint() -> None:
    client = APIClient()
    response = client.get(reverse("mirror-control-manifest-list"))
    assert response.status_code == 200
    assert b"mirror-control-plane" in response.content


def test_router_exposes_pipeline_endpoint() -> None:
    client = APIClient()
    response = client.get(reverse("pipeline-list"))
    assert response.status_code == 200
