"""Middleware execution context models."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MiddlewareContext(BaseModel):
    """Frozen metadata for middleware-scoped execution state."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    run_id: UUID | None = None
    pipeline_id: str | None = None
    step_id: str | None = None
    capability: str | None = None
    scope: str = "capability"
    metadata: dict[str, Any] = Field(default_factory=dict)
