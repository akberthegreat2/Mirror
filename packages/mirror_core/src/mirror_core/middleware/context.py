"""Middleware execution context models."""

from __future__ import annotations

from mirror_core.execution import CapabilityContext


class MiddlewareContext(CapabilityContext):
    """Backward-compatible name for capability-scoped middleware context."""

    scope: str = "capability"
