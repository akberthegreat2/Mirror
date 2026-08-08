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


def test_pipeline_versions_are_created_but_not_updated() -> None:
    from mirror_control_django.models import Pipeline, Project

    project = Project.objects.create(slug="api", name="API")
    pipeline = Pipeline.objects.create(
        project=project,
        slug="managed",
        name="Managed",
        origin="managed",
    )
    client = APIClient()
    response = client.post(
        reverse("pipelineversion-list"),
        {
            "pipeline": pipeline.pk,
            "definition_text": '{"id":"managed","steps":[{"id":"crawl","capability":"crawl"}]}',
            "notes": "first",
            "metadata": {},
        },
        format="json",
    )
    assert response.status_code == 201
    version_id = response.data["id"]
    update = client.patch(
        reverse("pipelineversion-detail", args=[version_id]),
        {"notes": "mutated"},
        format="json",
    )
    assert update.status_code == 405
