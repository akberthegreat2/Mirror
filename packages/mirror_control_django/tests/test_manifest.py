"""Manifest tests for the Mirror control plane."""

from __future__ import annotations

from mirror_control_django.manifest import control_plane_manifest


def test_manifest_contains_expected_entities() -> None:
    manifest = control_plane_manifest()
    names = manifest.entity_names()
    assert "pipeline" in names
    assert "execution-run" in names
    assert manifest.get("pipeline").blob_backed is True
