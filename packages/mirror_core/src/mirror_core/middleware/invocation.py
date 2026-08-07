"""Typed middleware invocation payload."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.execution import CapabilityContext, ExecutionContext
from mirror_core.middleware.context import MiddlewareContext
from mirror_core.pipeline import Step


class MiddlewareInvocation(BaseModel):
    """Frozen payload passed through the middleware chain."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    step: Step
    request: BaseModel
    provider: Any
    execution_context: ExecutionContext
    capability_context: CapabilityContext
    context: dict[str, Any] = Field(default_factory=dict)
    middleware_context: MiddlewareContext | None = None
