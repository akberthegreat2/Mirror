"""Django app configuration for Mirror Control Panel."""

from django.apps import AppConfig


class MirrorControlPanelConfig(AppConfig):
    """App config for Mirror Control Panel."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "mirror_control_panel"
    verbose_name = "Mirror Control Panel"

    def ready(self) -> None:
        """Import signals when Django is ready."""
        # Import signals to register signal handlers
        from mirror_control_panel import signals  # noqa: F401
