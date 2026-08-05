"""Mirror control-plane manifest and Django settings helpers.

Mirror uses Django as the control plane for metadata, admin pages, auth, and
operator workflows. This module describes that control plane without importing
Django unless a caller explicitly asks for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec


@dataclass(frozen=True, slots=True)
class ControlPlaneModelSpec:
    """Describe one metadata model needed by the Django control plane."""

    name: str
    fields: tuple[str, ...]
    admin_list_display: tuple[str, ...] = ()
    admin_search_fields: tuple[str, ...] = ()
    admin_readonly_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ControlPlaneSpec:
    """Describe the Django-facing control plane for a Mirror project."""

    app_label: str
    admin_site_name: str
    installed_apps: tuple[str, ...]
    models: tuple[ControlPlaneModelSpec, ...]

    def model_names(self) -> tuple[str, ...]:
        """Return the model names in declaration order."""
        return tuple(model.name for model in self.models)

    def summary_lines(self) -> tuple[str, ...]:
        """Return human-readable summary lines for docs and templates."""
        lines = [
            f"App label: {self.app_label}",
            f"Admin site: {self.admin_site_name}",
            "Installed apps:",
        ]
        lines.extend(f"  - {name}" for name in self.installed_apps)
        lines.append("Models:")
        lines.extend(f"  - {model.name}" for model in self.models)
        return tuple(lines)


DEFAULT_MODELS: tuple[ControlPlaneModelSpec, ...] = (
    ControlPlaneModelSpec(
        name="Project",
        fields=("name", "slug", "created_at"),
        admin_list_display=("name", "slug", "created_at"),
        admin_search_fields=("name", "slug"),
    ),
    ControlPlaneModelSpec(
        name="Pipeline",
        fields=("project", "name", "version", "enabled"),
        admin_list_display=("project", "name", "version", "enabled"),
        admin_search_fields=("project__name", "name"),
    ),
    ControlPlaneModelSpec(
        name="PipelineRun",
        fields=("pipeline", "status", "started_at", "finished_at"),
        admin_list_display=("pipeline", "status", "started_at", "finished_at"),
        admin_search_fields=("pipeline__name", "status"),
    ),
    ControlPlaneModelSpec(
        name="PipelineStep",
        fields=("run", "step_id", "status", "started_at", "finished_at"),
        admin_list_display=("run", "step_id", "status", "started_at", "finished_at"),
        admin_search_fields=("run__id", "step_id", "status"),
    ),
    ControlPlaneModelSpec(
        name="CrawledUrl",
        fields=("project", "url", "status", "depth", "discovered_at"),
        admin_list_display=("project", "url", "status", "depth", "discovered_at"),
        admin_search_fields=("url", "status"),
    ),
    ControlPlaneModelSpec(
        name="ArchiveRecord",
        fields=("project", "resource_id", "blob_key", "archived_at"),
        admin_list_display=("project", "resource_id", "blob_key", "archived_at"),
        admin_search_fields=("resource_id", "blob_key"),
    ),
    ControlPlaneModelSpec(
        name="Worker",
        fields=("project", "name", "backend", "status", "last_heartbeat_at"),
        admin_list_display=("project", "name", "backend", "status", "last_heartbeat_at"),
        admin_search_fields=("name", "backend", "status"),
    ),
    ControlPlaneModelSpec(
        name="Schedule",
        fields=("project", "name", "cron", "enabled"),
        admin_list_display=("project", "name", "cron", "enabled"),
        admin_search_fields=("name", "cron"),
    ),
    ControlPlaneModelSpec(
        name="Checkpoint",
        fields=("run", "step_id", "blob_key", "created_at"),
        admin_list_display=("run", "step_id", "blob_key", "created_at"),
        admin_search_fields=("run__id", "step_id", "blob_key"),
    ),
)

DEFAULT_INSTALLED_APPS: tuple[str, ...] = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mirror_control_django",
)


def default_control_plane_spec() -> ControlPlaneSpec:
    """Return the canonical Mirror control-plane specification."""
    return ControlPlaneSpec(
        app_label="mirror_control_django",
        admin_site_name="mirror-control",
        installed_apps=DEFAULT_INSTALLED_APPS,
        models=DEFAULT_MODELS,
    )


def ensure_django_available() -> None:
    """Raise a helpful error if Django is not installed."""
    if find_spec("django") is None:
        raise RuntimeError(
            "Django is required for the control-plane adapter. "
            "Install Mirror with the Django extra or install Django separately."
        )


def render_django_settings_fragment(spec: ControlPlaneSpec | None = None) -> str:
    """Render a minimal Django settings fragment for the control plane."""
    spec = spec or default_control_plane_spec()
    apps = ",\n    ".join(f'"{app}"' for app in spec.installed_apps)
    model_lines = ",\n        ".join(f'"{name}"' for name in spec.model_names())
    return (
        "INSTALLED_APPS = [\n"
        f"    {apps},\n"
        "]\n\n"
        "MIRROR_CONTROL_PLANE = {\n"
        f'    "app_label": "{spec.app_label}",\n'
        f'    "admin_site_name": "{spec.admin_site_name}",\n'
        "    \"models\": [\n"
        f"        {model_lines}\n"
        "    ],\n"
        "}\n"
    )
