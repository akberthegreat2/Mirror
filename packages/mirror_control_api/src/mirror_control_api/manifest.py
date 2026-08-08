"""Manifest for the Mirror REST control-plane interface."""

from mirror_core.extensions.models import InterfaceManifest

interface = InterfaceManifest(
    name="rest",
    interface_type="api",
    factory="mirror_control_api.views:ManifestViewSet",
    requires_capabilities=[],
    metadata={
        "description": "Django REST Framework control-plane API for Mirror metadata and pipeline operations."
    },
)

__all__ = ["interface"]
