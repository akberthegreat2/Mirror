"""Tracing middleware for request context propagation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from mirror_core.middleware import Invocation, NextMiddleware
from mirror_core.registry import MiddlewareConfig


class TracingSettings(BaseModel):
    """Validated settings for tracing middleware."""

    model_config = ConfigDict(frozen=True)

    service_name: str = "mirror"
    exporter: str = "console"


class TracingMiddleware:
    """Propagate basic run and step context through the invocation chain."""

    def __init__(self, settings: TracingSettings | None = None, /, **overrides: Any) -> None:
        if settings is None:
            settings = TracingSettings.model_validate(overrides)
        elif overrides:
            settings = settings.model_copy(update=overrides)
        self.settings = settings

    async def __call__(self, invocation: Invocation, next_middleware: NextMiddleware) -> Any:
        """Attach trace context and continue."""
        trace = invocation.context.setdefault("trace", {})
        trace.setdefault("service_name", self.settings.service_name)
        trace.setdefault("step_id", invocation.step.id)
        trace.setdefault("capability", invocation.step.capability)
        run_id = invocation.context.get("run_id")
        if run_id is not None:
            trace.setdefault("run_id", str(run_id))
        return await next_middleware(invocation)


middleware = MiddlewareConfig(
    name="tracing",
    factory="mirror_middleware.tracing:TracingMiddleware",
    settings_model=TracingSettings,
    applies_to=None,
    after=["logging"],
    metadata={
        "description": "Basic execution context propagation",
    },
)


def middleware_config() -> MiddlewareConfig:
    """Return the middleware descriptor for compatibility."""
    return middleware
