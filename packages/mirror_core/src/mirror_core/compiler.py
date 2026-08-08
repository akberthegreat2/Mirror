"""Trusted pipeline compiler for Mirror Core.

ADR-0027 gives pipeline compilation a named owner so raw pipeline definitions
are parsed and validated before planning begins. The compiler stays a thin
facade over the planner, which keeps the runtime kernel singular while still
making the compilation boundary explicit.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from mirror_core.exceptions import PlannerError
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.pipeline import Pipeline
from mirror_core.planner import ExecutionPlan, Planner


class PipelineCompiler:
    """Parse and validate pipelines before handing them to the planner."""

    def __init__(
        self,
        registry: ExtensionRegistryManager,
        default_providers: dict[str, str] | None = None,
    ) -> None:
        """Create a compiler bound to a registry and default providers."""
        self._registry = registry
        self._default_providers = dict(default_providers or {})

    def compile(
        self,
        pipeline: Pipeline | Mapping[str, Any],
    ) -> ExecutionPlan:
        """Parse, validate, and compile a declarative pipeline definition."""
        try:
            pipeline_model = pipeline if isinstance(pipeline, Pipeline) else Pipeline.model_validate(pipeline)
        except PydanticValidationError as exc:
            raise PlannerError("Invalid pipeline definition", cause=exc) from exc
        return Planner(
            self._registry,
            default_providers=self._default_providers,
        ).plan(pipeline_model)
