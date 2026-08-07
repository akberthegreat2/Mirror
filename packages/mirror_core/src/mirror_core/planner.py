"""Compile declarative pipelines into immutable execution plans."""

from __future__ import annotations

import hashlib
from collections import deque
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.exceptions import PlannerError
from mirror_core.execution import ExecutionPolicy
from mirror_core.extensions.models import CapabilityManifest, ProviderManifest
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.imports import resolve_type
from mirror_core.pipeline import Pipeline, Step


class CompiledStep(BaseModel):
    """A step with capability and provider identities resolved at compile time."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    definition: Step
    capability: CapabilityManifest
    provider: ProviderManifest
    dependencies: frozenset[str] = Field(default_factory=frozenset)
    fallback_providers: tuple[ProviderManifest, ...] = Field(default_factory=tuple)
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)

    @property
    def id(self) -> str:
        return self.definition.id


class ExecutionPlan(BaseModel):
    """Immutable plan consumed by the executor."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    pipeline_id: str
    steps: Mapping[str, CompiledStep]
    order: tuple[str, ...]
    parallel_groups: tuple[tuple[str, ...], ...]
    config_fingerprint: str
    input_names: frozenset[str] = Field(default_factory=frozenset)

    def model_post_init(self, __context: Any) -> None:
        """Freeze the compiled steps mapping after validation."""
        object.__setattr__(self, "steps", MappingProxyType(dict(self.steps)))

    def get_step(self, step_id: str) -> CompiledStep:
        try:
            return self.steps[step_id]
        except KeyError as exc:
            raise PlannerError(f"Unknown compiled step: {step_id}") from exc

    @property
    def step_ids(self) -> list[str]:
        return list(self.order)

    @property
    def dependencies(self) -> Mapping[str, frozenset[str]]:
        return MappingProxyType(
            {
                step_id: frozenset(step.dependencies)
                for step_id, step in self.steps.items()
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "steps": {
                step_id: {
                    "definition": compiled.definition.model_dump(mode="json"),
                    "capability": compiled.capability.name,
                    "capability_version": compiled.capability.api_version,
                    "provider": compiled.provider.name,
                    "fallback_providers": [
                        provider.name for provider in compiled.fallback_providers
                    ],
                    "dependencies": sorted(compiled.dependencies),
                    "policy": compiled.policy.model_dump(mode="json"),
                }
                for step_id, compiled in self.steps.items()
            },
            "order": list(self.order),
            "parallel_groups": [list(group) for group in self.parallel_groups],
            "config_fingerprint": self.config_fingerprint,
            "input_names": sorted(self.input_names),
        }


class Planner:
    """Validate a pipeline and resolve all runtime identities exactly once."""

    def __init__(
        self,
        registry: ExtensionRegistryManager,
        default_providers: dict[str, str] | None = None,
    ) -> None:
        self._registry = registry
        self._default_providers = default_providers or {}

    def plan(self, pipeline: Pipeline) -> ExecutionPlan:
        self._validate_unique_step_ids(pipeline)
        capabilities = self._resolve_capabilities(pipeline)
        self._validate_required_capabilities(capabilities)
        providers = self._resolve_providers(pipeline, capabilities)
        fallback_providers = self._resolve_fallback_providers(
            pipeline, capabilities, providers
        )
        dependencies, reverse_dependencies = self._build_dependency_graph(pipeline)
        order = self._topological_sort(pipeline, dependencies, reverse_dependencies)
        self._validate_bindings(pipeline, capabilities)

        groups = self._compute_parallel_groups(dependencies, order)

        compiled_steps = {
            step.id: CompiledStep(
                definition=step,
                capability=capabilities[step.id],
                provider=providers[step.id],
                dependencies=frozenset(dependencies[step.id]),
                fallback_providers=tuple(fallback_providers[step.id]),
                policy=ExecutionPolicy.from_step(step),
            )
            for step in pipeline.steps
        }
        fingerprint = hashlib.sha256(pipeline.model_dump_json().encode()).hexdigest()
        return ExecutionPlan(
            pipeline_id=pipeline.id,
            steps=compiled_steps,
            order=tuple(order),
            parallel_groups=tuple(tuple(group) for group in groups),
            config_fingerprint=fingerprint,
            input_names=frozenset(pipeline.inputs),
        )

    @staticmethod
    def _validate_unique_step_ids(pipeline: Pipeline) -> None:
        step_ids = [step.id for step in pipeline.steps]
        duplicates = sorted(
            {step_id for step_id in step_ids if step_ids.count(step_id) > 1}
        )
        if duplicates:
            raise PlannerError(f"Duplicate pipeline step IDs: {', '.join(duplicates)}")

    def _resolve_capabilities(
        self, pipeline: Pipeline
    ) -> dict[str, CapabilityManifest]:
        resolved: dict[str, CapabilityManifest] = {}
        for step in pipeline.steps:
            try:
                resolved[step.id] = self._registry.resolve_capability(step.capability)
            except Exception as exc:
                raise PlannerError(
                    f"Unknown capability {step.capability!r} in step {step.id!r}",
                    cause=exc,
                ) from exc
        return resolved

    def _validate_required_capabilities(
        self, capabilities: dict[str, CapabilityManifest]
    ) -> None:
        required = sorted(
            {
                (dependency.target, dependency.version_constraint)
                for capability in capabilities.values()
                for dependency in capability.dependencies
            }
        )
        for dependency_name, dependency_version in required:
            try:
                self._registry.resolve_capability(dependency_name, dependency_version)
            except Exception as exc:
                constraint = (
                    dependency_version
                    if dependency_version is not None
                    else "any version"
                )
                raise PlannerError(
                    f"Required capability {dependency_name!r} ({constraint}) is not available",
                    cause=exc,
                ) from exc

    def _resolve_providers(
        self,
        pipeline: Pipeline,
        capabilities: dict[str, CapabilityManifest],
    ) -> dict[str, ProviderManifest]:
        resolved: dict[str, ProviderManifest] = {}
        for step in pipeline.steps:
            requested = step.provider or self._default_providers.get(step.capability)
            try:
                resolved[step.id] = self._registry.resolve_provider(
                    capabilities[step.id], requested
                )
            except Exception as exc:
                raise PlannerError(
                    f"Unable to resolve provider for step {step.id!r} "
                    f"({step.capability!r})",
                    cause=exc,
                ) from exc
        return resolved

    def _resolve_fallback_providers(
        self,
        pipeline: Pipeline,
        capabilities: dict[str, CapabilityManifest],
        primary: dict[str, ProviderManifest],
    ) -> dict[str, list[ProviderManifest]]:
        resolved: dict[str, list[ProviderManifest]] = {}
        for step in pipeline.steps:
            fallback = step.fallback.providers if step.fallback is not None else ()
            providers: list[ProviderManifest] = []
            seen: set[str] = set()
            for provider_name in fallback:
                if provider_name in seen or provider_name == primary[step.id].name:
                    continue
                try:
                    provider = self._registry.resolve_provider(
                        capabilities[step.id], provider_name
                    )
                except Exception as exc:
                    raise PlannerError(
                        f"Unable to resolve fallback provider {provider_name!r} "
                        f"for step {step.id!r}",
                        cause=exc,
                    ) from exc
                providers.append(provider)
                seen.add(provider.name)
            resolved[step.id] = providers
        return resolved

    def _validate_bindings(
        self,
        pipeline: Pipeline,
        capabilities: dict[str, CapabilityManifest],
    ) -> None:
        steps_by_id = {step.id: step for step in pipeline.steps}
        for step in pipeline.steps:
            capability = capabilities[step.id]
            available_outputs = set(capability.output_ports)
            result_model = resolve_type(capability.result_model)
            if result_model is not None:
                available_outputs.update(
                    getattr(result_model, "model_fields", {}).keys()
                )
                available_outputs.add("result")
            unknown_outputs = sorted(set(step.outputs).difference(available_outputs))
            if unknown_outputs:
                raise PlannerError(
                    f"Step {step.id!r} declares unknown outputs: {', '.join(unknown_outputs)}"
                )
            declared_inputs = set(capability.input_ports)
            request_model = resolve_type(capability.request_model)
            if not declared_inputs and request_model is not None:
                declared_inputs = set(getattr(request_model, "model_fields", {}).keys())

            for target, source in step.input.items():
                if declared_inputs and target not in declared_inputs:
                    raise PlannerError(
                        f"Step {step.id!r} binds undeclared input port {target!r}"
                    )
                source_step, source_output = self._parse_binding(source, step.id)
                if source_step == "$pipeline":
                    if source_output not in pipeline.inputs:
                        raise PlannerError(
                            f"Step {step.id!r} references undeclared pipeline input "
                            f"{source_output!r}"
                        )
                    continue
                if source_step not in steps_by_id:
                    raise PlannerError(
                        f"Step {step.id!r} references unknown step {source_step!r}"
                    )
                source_capability = capabilities[source_step]
                source_ports = set(source_capability.output_ports)
                source_result_model = resolve_type(source_capability.result_model)
                if source_result_model is not None:
                    source_ports.update(
                        getattr(source_result_model, "model_fields", {}).keys()
                    )
                if not source_ports:
                    source_ports = set(steps_by_id[source_step].outputs)
                if source_output not in source_ports:
                    raise PlannerError(
                        f"Step {step.id!r} references unknown output {source_output!r} "
                        f"from step {source_step!r}"
                    )
                self._validate_port_compatibility(
                    source_step,
                    source_output,
                    source_capability,
                    step.id,
                    target,
                    capability,
                )

    @staticmethod
    def _parse_binding(source: str, step_id: str) -> tuple[str, str]:
        if "." not in source:
            raise PlannerError(
                f"Step {step_id!r} has invalid binding {source!r}; expected '<step>.<output>'"
            )
        return tuple(source.split(".", 1))  # type: ignore[return-value]

    @staticmethod
    def _validate_port_compatibility(
        source_step: str,
        source_output: str,
        source_capability: CapabilityManifest,
        target_step: str,
        target_input: str,
        target_capability: CapabilityManifest,
    ) -> None:
        source_type: Any = source_capability.output_ports.get(source_output)
        source_result_model = resolve_type(source_capability.result_model)
        if source_type is None and source_result_model is not None:
            field = getattr(source_result_model, "model_fields", {}).get(source_output)
            source_type = field.annotation if field is not None else None
        target_type: Any = target_capability.input_ports.get(target_input)
        target_request_model = resolve_type(target_capability.request_model)
        if target_type is None and target_request_model is not None:
            field = getattr(target_request_model, "model_fields", {}).get(target_input)
            target_type = field.annotation if field is not None else None
        if source_type is None or target_type is None or source_type == target_type:
            return
        if (
            isinstance(source_type, type)
            and isinstance(target_type, type)
            and issubclass(source_type, target_type)
        ):
            return
        source_name = getattr(source_type, "__name__", str(source_type))
        target_name = getattr(target_type, "__name__", str(target_type))
        raise PlannerError(
            f"Incompatible binding {source_step}.{source_output} ({source_name}) "
            f"-> {target_step}.{target_input} ({target_name})"
        )

    def _build_dependency_graph(
        self, pipeline: Pipeline
    ) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
        dependencies: dict[str, set[str]] = {step.id: set() for step in pipeline.steps}
        reverse: dict[str, set[str]] = {step.id: set() for step in pipeline.steps}
        for step in pipeline.steps:
            for source in step.input.values():
                source_step, _ = self._parse_binding(source, step.id)
                if source_step == "$pipeline":
                    continue
                dependencies[step.id].add(source_step)
                reverse[source_step].add(step.id)
        return dependencies, reverse

    @staticmethod
    def _topological_sort(
        pipeline: Pipeline,
        dependencies: dict[str, set[str]],
        reverse_dependencies: dict[str, set[str]],
    ) -> list[str]:
        in_degree = {step.id: len(dependencies[step.id]) for step in pipeline.steps}
        queue = deque(step.id for step in pipeline.steps if in_degree[step.id] == 0)
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for dependent in sorted(reverse_dependencies[node]):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        if len(order) != len(in_degree):
            raise PlannerError("Cycle detected in pipeline graph")
        return order

    @staticmethod
    def _compute_parallel_groups(
        dependencies: dict[str, set[str]], order: list[str]
    ) -> list[list[str]]:
        level: dict[str, int] = {}
        for step_id in order:
            level[step_id] = (
                0
                if not dependencies[step_id]
                else 1 + max(level[dependency] for dependency in dependencies[step_id])
            )
        groups: dict[int, list[str]] = {}
        for step_id in order:
            groups.setdefault(level[step_id], []).append(step_id)
        return [groups[index] for index in sorted(groups)]
