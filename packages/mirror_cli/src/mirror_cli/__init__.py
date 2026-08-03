"""Mirror CLI interface – dynamic command discovery."""

from mirror_core.registry import InterfaceConfig

from mirror_cli.main import app

# Interface descriptor for discovery
interface = InterfaceConfig(
    name="cli",
    interface_type="cli",
    factory="mirror_cli.main:app",
    requires_capabilities=[],
    metadata={
        "description": "Command-line interface for Mirror",
    },
)

__all__ = ["app", "interface"]
