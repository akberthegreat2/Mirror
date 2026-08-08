"""Repository tests for pipeline materialization."""

from __future__ import annotations

from pathlib import Path

from mirror_control_django.repository import ControlPlaneRepository, deserialize_pipeline_definition
from mirror_core.pipeline import Pipeline, Step


def test_materialize_pipeline_roundtrip(tmp_path: Path) -> None:
    from mirror_control_django import models

    repo = ControlPlaneRepository(blob_store=None)
    repo.blob_store = repo.blob_store.__class__(tmp_path / "blobs")

    pipeline = Pipeline(
        id="crawl-site",
        steps=[Step(id="crawl", capability="crawl")],
        inputs={"url": "string"},
    )

    managed, version = repo.materialize_pipeline(
        project_slug="demo",
        pipeline_slug="crawl-site",
        pipeline=pipeline,
        metadata={"owner": "alice"},
    )

    assert managed.slug == "crawl-site"
    assert version.version == 1
    blob = repo.blob_store.get_bytes(version.definition_ref)
    assert blob is not None
    restored = deserialize_pipeline_definition(blob)
    assert restored.id == pipeline.id
    assert models.Pipeline.objects.count() == 1
