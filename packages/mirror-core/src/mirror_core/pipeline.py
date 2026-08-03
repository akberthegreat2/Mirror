"""DAG pipeline model with steps, conditions, and policies."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RetryPolicy = dict[str, Any]  # {"attempts": 3, "backoff": "exponential", "jitter": 0.1}
ErrorPolicy = Literal["abort", "continue", "skip", "fallback"]


class Step(BaseModel):
    """A single step in a pipeline DAG."""

    model_config = ConfigDict(frozen=True)

    id: str
    capability: str
    provider: str | None = None  # optional, uses default from settings
    input: dict[str, str] = Field(default_factory=dict)  # bindings
    outputs: list[str] = Field(default_factory=list)
    condition: str | None = None  # safe expression language
    retry: RetryPolicy | None = None
    timeout: float | None = Field(default=None, gt=0.0)
    on_error: ErrorPolicy = "abort"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Pipeline(BaseModel):
    """A complete DAG pipeline definition."""

    id: str
    version: str = "1.0"
    steps: list[Step]
    inputs: dict[str, str] = Field(default_factory=dict)  # pipeline-level inputs
    outputs: list[str] = Field(default_factory=list)  # pipeline-level outputs
    metadata: dict[str, Any] = Field(default_factory=dict)
