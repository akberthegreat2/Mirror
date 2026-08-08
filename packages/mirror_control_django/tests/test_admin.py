"""Admin registry tests for the Mirror control plane."""

from __future__ import annotations

from django.contrib import admin

from mirror_control_django import models


def test_admin_registers_key_models() -> None:
    registry = admin.site._registry
    assert models.Project in registry
    assert models.Pipeline in registry
    assert models.PipelineVersion in registry
    assert models.ExecutionRun in registry
    assert models.Worker in registry
