"""Execution context and policy models for Mirror Core.

ADR-0025 introduces explicit runtime contracts for per-run execution state,
capability-scoped invocation state, and execution policies. The executor and
planner use these models internally so middleware and runners can observe the
same runtime facts without owning orchestration logic.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from mirror_core.pipeline import (
    CheckpointPolicy,
    CompensationPolicy,
    ErrorPolicy,
    FallbackPolicy,
    RetryPolicy,
    Step,
)
from mirror_core.resource import ResourceEnvelope


class ExecutionPolicy(BaseModel):
    """Immutable policy resolved for a compiled pipeline step."""

    model_config = ConfigDict(frozen=True)

    retry: RetryPolicy | None = None
    fallback: FallbackPolicy | None = None
    checkpoint: CheckpointPolicy | None = None
    compensation: CompensationPolicy | None = None
    timeout: float | None = Field(default=None, gt=0.0)
    on_error: ErrorPolicy = "abort"

    @classmethod
    def from_step(cls, step: Step) -> ExecutionPolicy:
        """Build an execution policy from a declarative pipeline step."""
        return cls(
            retry=step.retry,
            fallback=step.fallback,
            checkpoint=step.checkpoint,
            compensation=step.compensation,
            timeout=step.timeout,
            on_error=step.on_error,
        )


class ExecutionContext(BaseModel):
    """Immutable snapshot of a single execution run."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    run_id: UUID
    pipeline_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    inputs: Mapping[str, Any] = Field(default_factory=dict)
    results: Mapping[str, ResourceEnvelope] = Field(default_factory=dict)
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any, /) -> None:
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        object.__setattr__(self, "results", MappingProxyType(dict(self.results)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @field_serializer("inputs")
    def _serialize_inputs(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)

    @field_serializer("results")
    def _serialize_results(
        self, value: Mapping[str, ResourceEnvelope]
    ) -> dict[str, ResourceEnvelope]:
        return dict(value)

    @field_serializer("metadata")
    def _serialize_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)


class CapabilityContext(BaseModel):
    """Immutable capability-scoped view over a running execution."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    execution: ExecutionContext
    step_id: str
    capability: str
    capability_version: str
    provider: str
    provider_version: str | None = None
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any, /) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_execution(
        cls,
        execution: ExecutionContext,
        *,
        step_id: str,
        capability: str,
        capability_version: str,
        provider: str,
        provider_version: str | None = None,
        policy: ExecutionPolicy | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> CapabilityContext:
        """Build a capability-scoped context from a run snapshot."""
        return cls(
            execution=execution,
            step_id=step_id,
            capability=capability,
            capability_version=capability_version,
            provider=provider,
            provider_version=provider_version,
            policy=policy or ExecutionPolicy(),
            metadata=dict(metadata or {}),
        )

    @field_serializer("metadata")
    def _serialize_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)
