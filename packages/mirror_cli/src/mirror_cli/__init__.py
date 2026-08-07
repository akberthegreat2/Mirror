"""Mirror CLI interface – dynamic command discovery."""

from mirror_core.extensions.models import InterfaceManifest

from mirror_cli.main import app

# Interface descriptor for discovery
interface = InterfaceManifest(
    name="cli",
    interface_type="cli",
    factory="mirror_cli.main:app",
    requires_capabilities=[],
    metadata={
        "description": "Command-line interface for Mirror",
    },
)

__all__ = ["app", "interface"]
