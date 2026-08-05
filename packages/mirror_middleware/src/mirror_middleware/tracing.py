"""Tracing middleware for request context propagation."""

from __future__ import annotations

from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware
from mirror_core.registry import MiddlewareConfig


class TracingMiddleware:
    """Propagate basic run and step context through the invocation chain."""

    def __init__(
        self,
        service_name: str = "mirror",
        exporter: str = "console",
    ) -> None:
        self.service_name = service_name
        self.exporter = exporter

    async def __call__(self, invocation: Invocation, next_middleware: NextMiddleware) -> Any:
        """Attach trace context and continue."""
        trace = invocation.context.setdefault("trace", {})
        trace.setdefault("service_name", self.service_name)
        trace.setdefault("step_id", invocation.step.id)
        trace.setdefault("capability", invocation.step.capability)
        run_id = invocation.context.get("run_id")
        if run_id is not None:
            trace.setdefault("run_id", str(run_id))
        return await next_middleware(invocation)


middleware = MiddlewareConfig(
    name="tracing",
    factory="mirror_middleware.tracing:TracingMiddleware",
    settings_model=None,
    applies_to=None,
    after=["logging"],
    metadata={
        "description": "Basic execution context propagation",
    },
)


def middleware_config() -> MiddlewareConfig:
    """Return the middleware descriptor for compatibility."""
    return middleware
