"""Tracing middleware for OpenTelemetry integration (stub).

This is a placeholder for distributed tracing integration.
"""

from __future__ import annotations

from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware


class TracingMiddleware:
    """OpenTelemetry tracing middleware (stub).

    Settings:
        service_name (str): Name of the service. Default: "mirror".
        exporter (str): Exporter type (e.g., "console", "otlp"). Default: "console".
    """

    def __init__(
        self,
        service_name: str = "mirror",
        exporter: str = "console",
    ) -> None:
        self.service_name = service_name
        self.exporter = exporter
        # TODO: Initialize OpenTelemetry when dependencies are added

    async def __call__(self, invocation: Invocation, next_middleware: NextMiddleware) -> Any:
        """Execute with tracing."""
        # Placeholder: just call next
        # In full implementation, wrap with span
        return await next_middleware(invocation)


def middleware_config() -> dict[str, Any]:
    """Return middleware descriptor for discovery."""
    return {
        "name": "tracing",
        "factory": "mirror_middleware.tracing:TracingMiddleware",
        "settings_model": None,
        "applies_to": None,
        "ordering_constraints": {"after": ["logging"]},
        "metadata": {
            "description": "OpenTelemetry distributed tracing (stub)",
        },
    }
