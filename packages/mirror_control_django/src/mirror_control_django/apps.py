"""Django app configuration for the Mirror control plane."""

from __future__ import annotations

from django.apps import AppConfig


class MirrorControlDjangoConfig(AppConfig):
    """Django app config for the control-plane models and admin."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "mirror_control_django"
    verbose_name = "Mirror Control Plane"
