"""Interface-neutral projections of Mirror's extension catalog.

Interfaces such as the CLI, Django control plane, and REST API consume this
module instead of implementing their own manifest discovery and serialization.
The module is deliberately presentation-neutral: it does not know about
Typer, Django, DRF, HTTP, HTML, or terminal formatting.
"""

from __future__ import annotations

from typing import Any

from mirror_core.discovery import DiscoveryResult, DiscoverySource, discover


class InterfaceCatalog:
    """Build a stable, serializable view of discovered Mirror extensions."""

    def __init__(self, source: DiscoverySource | None = None) -> None:
        self._source = source

    def discover(self) -> DiscoveryResult:
        """Discover and classify all canonical extension manifests."""
        return discover(source=self._source)

    def document(self) -> dict[str, Any]:
        """Return a JSON-compatible catalog projection for interfaces."""
        result = self.discover()
        return {
            "capabilities": [manifest.model_dump(mode="json") for manifest in result.capabilities],
            "providers": [manifest.model_dump(mode="json") for manifest in result.providers],
            "middleware": [manifest.model_dump(mode="json") for manifest in result.middleware],
            "interfaces": [manifest.model_dump(mode="json") for manifest in result.interfaces],
            "errors": [list(error) for error in result.errors],
            "duplicates": [list(item) for item in result.duplicates],
        }


__all__ = ["InterfaceCatalog"]
