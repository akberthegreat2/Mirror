"""Repository tests for pipeline materialization."""

from __future__ import annotations

from pathlib import Path

from mirror_control_django.repository import (
    ControlPlaneRepository,
    deserialize_pipeline_definition,
)
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


def test_managed_pipeline_versions_are_immutable(tmp_path: Path) -> None:
    repo = ControlPlaneRepository(blob_store=None)
    repo.blob_store = repo.blob_store.__class__(tmp_path / "blobs")
    pipeline = Pipeline(id="managed", steps=[Step(id="one", capability="crawl")])

    managed, first = repo.materialize_pipeline(
        project_slug="demo",
        pipeline_slug="managed",
        pipeline=pipeline,
    )
    second_pipeline = Pipeline(
        id="managed",
        steps=[Step(id="one", capability="fetch")],
    )
    _, second = repo.materialize_pipeline(
        project_slug="demo",
        pipeline_slug="managed",
        pipeline=second_pipeline,
    )

    managed.refresh_from_db()
    assert managed.current_version_number == 2
    assert first.version == 1
    assert second.version == 2
    assert first.definition_hash != second.definition_hash
    assert repo.load_pipeline_definition(first).steps[0].capability == "crawl"
    assert repo.load_pipeline_definition(second).steps[0].capability == "fetch"
