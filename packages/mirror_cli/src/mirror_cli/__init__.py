"""Mirror CLI interface – dynamic command discovery."""

from mirror_core.extensions.models import InterfaceManifest

from mirror_cli.main import app

# Interface manifest for discovery
interface = InterfaceManifest(
    name="cli",
    version="0.1.0",
    package_name="mirror-cli",
    api_version="1.0",
    requires_core=">=0.1.0",
    settings_model=None,
    interface_type="cli",
    factory="mirror_cli.main:app",
    requires_capabilities=[],
    metadata={
        "description": "Command-line interface for Mirror",
    },
)

__all__ = ["app", "interface"]
