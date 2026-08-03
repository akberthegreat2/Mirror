"""Mirror CLI interface – dynamic command discovery."""

from mirror_cli.main import app

__all__ = ["app"]

# Interface descriptor for discovery
interface = {
    "name": "cli",
    "interface_type": "cli",
    "factory": "mirror_cli.main:app",
    "requires_capabilities": [],
    "metadata": {
        "description": "Command-line interface for Mirror",
    },
}
