"""Django app configuration for the Mirror REST control-plane API."""

from __future__ import annotations

from django.apps import AppConfig


class MirrorControlAPIConfig(AppConfig):
    """Django app config for the REST interface."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "mirror_control_api"
    verbose_name = "Mirror Control API"
