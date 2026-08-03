"""Pipeline planner: validates graph, detects cycles, topological sort."""

from __future__ import annotations

import hashlib
from collections import deque
from typing import Any

from mirror_core.exceptions import PlannerError
from mirror_core.pipeline import Pipeline, Step


class ExecutionPlan:
    def __init__(
        self,
        pipeline_id: str,
        steps: list[Step],
        order: list[str],
        parallel_groups: list[list[str]],
        dependencies: dict[str, set[str]],
        config_fingerprint: str,
        pipeline_inputs: dict[str, str] | None = None,
    ):
        self.pipeline_id = pipeline_id
        self.steps = {step.id: step for step in steps}
        self.order = order
        self.parallel_groups = parallel_groups
        self.dependencies = dependencies
        self.config_fingerprint = config_fingerprint
        self._step_list = steps
        self.pipeline_inputs = pipeline_inputs or {}

    def get_step(self, step_id: str) -> Step:
        return self.steps[step_id]

    @property
    def step_ids(self) -> list[str]:
        return self.order

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "steps": [s.model_dump() for s in self._step_list],
            "order": self.order,
            "parallel_groups": self.parallel_groups,
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "config_fingerprint": self.config_fingerprint,
        }


class Planner:
    def __init__(self, registry: Any):
        self._registry = registry

    def plan(self, pipeline: Pipeline) -> ExecutionPlan:
        self._validate_capabilities(pipeline)
        self._validate_bindings(pipeline)

        deps, reverse_deps = self._build_dependency_graph(pipeline)
        self._detect_cycles(pipeline, deps)

        order = self._topological_sort(pipeline, deps, reverse_deps)
        parallel_groups = self._compute_parallel_groups(pipeline, deps, order)

        fingerprint = hashlib.sha256(pipeline.model_dump_json().encode()).hexdigest()

        return ExecutionPlan(
            pipeline_id=pipeline.id,
            steps=pipeline.steps,
            order=order,
            parallel_groups=parallel_groups,
            dependencies=deps,
            config_fingerprint=fingerprint,
            pipeline_inputs=pipeline.inputs,
        )

    def _validate_capabilities(self, pipeline: Pipeline) -> None:
        for step in pipeline.steps:
            try:
                version = self._get_latest_capability_version(step.capability)
                self._registry.get_capability(step.capability, version)
            except Exception as e:
                raise PlannerError(
                    f"Unknown capability '{step.capability}' in step '{step.id}'",
                    cause=e,
                ) from e

    def _get_latest_capability_version(self, capability_name: str) -> str:
        """Get the latest registered version for a capability."""
        all_keys = self._registry.list_capabilities()
        matching: list[str] = [k for k in all_keys if k.startswith(f"{capability_name}:")]
        if not matching:
            raise PlannerError(f"No registered versions found for capability '{capability_name}'")
        # Sort versions semantically (simple string sort for alpha)
        matching.sort()
        # Extract version part: "capability:1.0" -> "1.0"
        return matching[-1].split(":", 1)[1]

    def _validate_bindings(self, pipeline: Pipeline) -> None:
        outputs: dict[str, set[str]] = {step.id: set(step.outputs) for step in pipeline.steps}
        outputs["$pipeline"] = set(pipeline.inputs.keys())

        for step in pipeline.steps:
            for _, source in step.input.items():
                if "." in source:
                    src_step, src_output = source.split(".", 1)
                    if src_step == "$pipeline":
                        continue
                    if src_step not in outputs:
                        raise PlannerError(f"Step '{step.id}' references unknown step '{src_step}'")
                    if src_output not in outputs[src_step]:
                        raise PlannerError(
                            f"Step '{step.id}' references unknown output '{src_output}' "
                            f"from step '{src_step}'"
                        )

    def _build_dependency_graph(
        self, pipeline: Pipeline
    ) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
        deps: dict[str, set[str]] = {step.id: set() for step in pipeline.steps}
        reverse_deps: dict[str, set[str]] = {step.id: set() for step in pipeline.steps}

        for step in pipeline.steps:
            for _, source in step.input.items():
                if "." in source:
                    src_step, _ = source.split(".", 1)
                    if src_step == "$pipeline":
                        continue
                    deps[step.id].add(src_step)
                    reverse_deps.setdefault(src_step, set()).add(step.id)

        return deps, reverse_deps

    def _detect_cycles(self, pipeline: Pipeline, deps: dict[str, set[str]]) -> None:
        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(node: str) -> None:
            visited.add(node)
            stack.add(node)
            for neighbor in deps.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in stack:
                    raise PlannerError(f"Cycle detected: {node} -> {neighbor}")
            stack.remove(node)

        for step in pipeline.steps:
            if step.id not in visited:
                dfs(step.id)

    def _topological_sort(
        self,
        pipeline: Pipeline,
        deps: dict[str, set[str]],
        reverse_deps: dict[str, set[str]],
    ) -> list[str]:
        in_degree: dict[str, int] = {step.id: len(deps[step.id]) for step in pipeline.steps}
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result: list[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for dependent in reverse_deps.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(in_degree):
            raise PlannerError("Cycle detected in pipeline graph")
        return result

    def _compute_parallel_groups(
        self,
        pipeline: Pipeline,
        deps: dict[str, set[str]],
        order: list[str],
    ) -> list[list[str]]:
        groups: list[list[str]] = []
        remaining = set(order)

        while remaining:
            group: list[str] = []
            for node in list(remaining):
                if all(dep not in remaining for dep in deps.get(node, set())):
                    group.append(node)
            if not group:
                raise PlannerError("Failed to compute parallel groups")
            for node in group:
                remaining.remove(node)
            groups.append(group)

        return groups
