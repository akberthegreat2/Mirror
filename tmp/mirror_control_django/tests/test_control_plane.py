"""Tests for the Django control-plane manifest."""

from __future__ import annotations

import pytest

from mirror_control_django import (
    default_control_plane_spec,
    ensure_django_available,
    render_django_settings_fragment,
)


def test_default_control_plane_contains_core_models() -> None:
    """The manifest should expose the models the control plane needs."""
    spec = default_control_plane_spec()
    assert spec.app_label == "mirror_control_django"
    assert spec.admin_site_name == "mirror-control"
    assert "django.contrib.admin" in spec.installed_apps
    assert "Project" in spec.model_names()
    assert "PipelineRun" in spec.model_names()
    assert "CrawledUrl" in spec.model_names()
    assert "Worker" in spec.model_names()


def test_render_django_settings_fragment_mentions_control_plane() -> None:
    """The rendered settings fragment should be copy-paste friendly."""
    text = render_django_settings_fragment()
    assert "INSTALLED_APPS" in text
    assert "mirror_control_django" in text
    assert "MIRROR_CONTROL_PLANE" in text
    assert "admin_site_name" in text
    assert "mirror-control" in text


def test_ensure_django_available_raises_helpful_error() -> None:
    """Projects without Django should get a clear error message."""
    with pytest.raises(RuntimeError, match="Django is required"):
        ensure_django_available()
