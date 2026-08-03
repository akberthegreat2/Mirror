"""Pipeline planner: validates graph, detects cycles, topological sort.

The planner produces an immutable ExecutionPlan that the executor can run.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from mirror_core.exceptions import PlannerError
from mirror_core.pipeline import Pipeline, Step


class ExecutionPlan:
    """Immutable execution plan produced by the planner."""

    def __init__(
        self,
        pipeline_id: str,
        steps: list[Step],
        order: list[str],
        parallel_groups: list[list[str]],
        dependencies: dict[str, set[str]],
        config_fingerprint: str,
    ) -> None:
        self.pipeline_id = pipeline_id
        self.steps = {step.id: step for step in steps}
        self.order = order
        self.parallel_groups = parallel_groups
        self.dependencies = dependencies
        self.config_fingerprint = config_fingerprint
        self._step_list = steps

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
    """Planner validates pipelines and produces execution plans."""

    def __init__(self, registry: Any) -> None:  # Registry type
        self._registry = registry

    def plan(self, pipeline: Pipeline) -> ExecutionPlan:
        """Validate and compile a pipeline into an execution plan.

        Steps:
            1. Validate all capability names exist in registry.
            2. Validate input bindings resolve to existing outputs.
            3. Build dependency graph.
            4. Detect cycles.
            5. Topological sort.
            6. Compute parallel groups.

        Raises:
            PlannerError: If validation fails or cycles are detected.
        """
        self._validate_capabilities(pipeline)
        self._validate_bindings(pipeline)

        dependencies = self._build_dependency_graph(pipeline)
        self._detect_cycles(pipeline, dependencies)

        order = self._topological_sort(pipeline, dependencies)
        parallel_groups = self._compute_parallel_groups(pipeline, dependencies, order)

        # Generate fingerprint from pipeline definition
        import hashlib
        import json

        fingerprint = hashlib.sha256(
            pipeline.model_dump_json().encode()
        ).hexdigest()

        return ExecutionPlan(
            pipeline_id=pipeline.id,
            steps=pipeline.steps,
            order=order,
            parallel_groups=parallel_groups,
            dependencies=dependencies,
            config_fingerprint=fingerprint,
        )

    def _validate_capabilities(self, pipeline: Pipeline) -> None:
        """Check that every step's capability exists in the registry."""
        for step in pipeline.steps:
            try:
                self._registry.get_capability(step.capability, "1.0")  # TODO: version
            except Exception as e:
                raise PlannerError(
                    f"Unknown capability '{step.capability}' in step '{step.id}'",
                    cause=e,
                )

    def _validate_bindings(self, pipeline: Pipeline) -> None:
        """Check that all input bindings resolve to existing outputs."""
        # Collect all outputs by step id
        outputs: dict[str, set[str]] = {}
        for step in pipeline.steps:
            outputs[step.id] = set(step.outputs)

        # Add pipeline inputs as available sources
        for input_name in pipeline.inputs:
            outputs["$pipeline"] = outputs.get("$pipeline", set()) | {input_name}

        for step in pipeline.steps:
            for target, source in step.input.items():
                if "." in source:
                    src_step, src_output = source.split(".", 1)
                    if src_step not in outputs:
                        raise PlannerError(
                            f"Step '{step.id}' references unknown step '{src_step}'"
                        )
                    if src_output not in outputs[src_step]:
                        raise PlannerError(
                            f"Step '{step.id}' references unknown output '{src_output}' "
                            f"from step '{src_step}'"
                        )
                else:
                    # Assume it's a pipeline input
                    if source not in pipeline.inputs:
                        raise PlannerError(
                            f"Step '{step.id}' references unknown input '{source}'"
                        )

    def _build_dependency_graph(
        self, pipeline: Pipeline
    ) -> dict[str, set[str]]:
        """Build dependency graph from step inputs."""
        deps: dict[str, set[str]] = {step.id: set() for step in pipeline.steps}

        for step in pipeline.steps:
            for target, source in step.input.items():
                if "." in source:
                    src_step, _ = source.split(".", 1)
                    deps[step.id].add(src_step)

        return deps

    def _detect_cycles(self, pipeline: Pipeline, deps: dict[str, set[str]]) -> None:
        """Detect cycles using DFS."""
        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(node: str) -> None:
            visited.add(node)
            stack.add(node)
            for neighbor in deps.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in stack:
                    raise PlannerError(f"Cycle detected involving step: {node} -> {neighbor}")
            stack.remove(node)

        for step in pipeline.steps:
            if step.id not in visited:
                dfs(step.id)

    def _topological_sort(
        self, pipeline: Pipeline, deps: dict[str, set[str]]
    ) -> list[str]:
        """Kahn's algorithm for topological sort."""
        in_degree: dict[str, int] = {step.id: 0 for step in pipeline.steps}
        for node, neighbors in deps.items():
            for neighbor in neighbors:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in deps.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(in_degree):
            raise PlannerError("Cycle detected in pipeline graph")

        return result

    def _compute_parallel_groups(
        self, pipeline: Pipeline, deps: dict[str, set[str]], order: list[str]
    ) -> list[list[str]]:
        """Group nodes that can run in parallel based on dependencies."""
        groups: list[list[str]] = []
        remaining = set(order)

        while remaining:
            group = []
            for node in list(remaining):
                if all(dep not in remaining for dep in deps.get(node, set())):
                    group.append(node)
            if not group:
                raise PlannerError("Failed to compute parallel groups")
            for node in group:
                remaining.remove(node)
            groups.append(group)

        return groups