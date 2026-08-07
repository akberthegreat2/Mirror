"""Tests for pipeline compilation."""

from types import MappingProxyType

import pytest
from mirror_core.exceptions import PlannerError
from mirror_core.extensions.models import (
    CapabilityManifest,
    Dependency,
    ProviderManifest,
)
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner
from pydantic import BaseModel


class TextInput(BaseModel):
    value: str


class TextOutput(BaseModel):
    result: str


def registry() -> ExtensionRegistryManager:
    result = ExtensionRegistryManager()
    result.register_capability(
        CapabilityManifest(
            name="fetch",
            api_version="1.10",
            request_model=TextInput,
            result_model=TextOutput,
            input_ports={"value": TextInput},
            output_ports={"result": TextOutput},
        )
    )
    result.register_capability(CapabilityManifest(name="fetch", api_version="1.9"))
    result.register_provider(
        ProviderManifest(
            name="httpx",
            capability="fetch",
            capability_api="~=1.0",
            factory="tests:test",
        )
    )
    return result


def test_planner_resolves_semantic_version_and_provider() -> None:
    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"value": "$pipeline.url"},
                outputs=["result"],
            )
        ],
        inputs={"url": "str"},
    )

    plan = Planner(registry(), default_providers={"fetch": "httpx"}).plan(pipeline)

    compiled = plan.get_step("a")
    assert compiled.capability.api_version == "1.10"
    assert compiled.provider.name == "httpx"
    assert plan.input_names == frozenset({"url"})


def test_planner_detects_cycle() -> None:
    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"value": "b.result"},
                outputs=["result"],
            ),
            Step(
                id="b",
                capability="fetch",
                input={"value": "a.result"},
                outputs=["result"],
            ),
        ],
    )

    with pytest.raises(PlannerError, match="Cycle detected"):
        Planner(registry(), default_providers={"fetch": "httpx"}).plan(pipeline)


def test_planner_rejects_undeclared_pipeline_input() -> None:
    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"value": "$pipeline.missing"},
                outputs=["result"],
            )
        ],
        inputs={"url": "str"},
    )

    with pytest.raises(PlannerError, match="undeclared pipeline input"):
        Planner(registry(), default_providers={"fetch": "httpx"}).plan(pipeline)


def test_planner_validates_required_capabilities() -> None:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="crawl",
            api_version="1.0",
            request_model=TextInput,
            result_model=TextOutput,
            output_ports={"result": TextOutput},
            dependencies=[Dependency(name="fetch", version="~=1.0")],
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="crawl", capability="crawl", capability_api="~=1.0", factory="x:y"
        )
    )
    pipeline = Pipeline(
        id="deps",
        steps=[Step(id="crawl", capability="crawl", outputs=["result"])],
    )

    with pytest.raises(
        PlannerError, match=r"Required capability 'fetch' \(~=1.0\) is not available"
    ):
        Planner(registry).plan(pipeline)


def test_port_assignability_is_directional() -> None:
    class Animal(BaseModel):
        name: str

    class Dog(Animal):
        breed: str

    class SourceRequest(BaseModel):
        value: str

    class TargetRequest(BaseModel):
        animal: Dog

    class TargetResult(BaseModel):
        ok: bool

    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="source",
            api_version="1.0",
            request_model=SourceRequest,
            result_model=Animal,
            output_ports={"result": Animal},
        )
    )
    registry.register_capability(
        CapabilityManifest(
            name="target",
            api_version="1.0",
            request_model=TargetRequest,
            result_model=TargetResult,
            input_ports={"animal": Dog},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="source", capability="source", capability_api="~=1.0", factory="x:y"
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="target", capability="target", capability_api="~=1.0", factory="x:y"
        )
    )
    pipeline = Pipeline(
        id="unsafe",
        inputs={"value": "str"},
        steps=[
            Step(id="source", capability="source", input={"value": "$pipeline.value"}),
            Step(id="target", capability="target", input={"animal": "source.result"}),
        ],
    )

    with pytest.raises(PlannerError, match="Incompatible binding"):
        Planner(registry).plan(pipeline)


def test_execution_plan_steps_are_deeply_immutable() -> None:
    """Compiled execution plans should expose read-only mappings."""

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"value": "$pipeline.url"},
                outputs=["result"],
            )
        ],
        inputs={"url": "str"},
    )

    plan = Planner(registry(), default_providers={"fetch": "httpx"}).plan(pipeline)

    assert isinstance(plan.steps, MappingProxyType)
    assert isinstance(plan.dependencies, MappingProxyType)

    with pytest.raises(TypeError):
        plan.steps["b"] = plan.get_step("a")  # type: ignore[index]

    with pytest.raises(TypeError):
        plan.dependencies["a"] = frozenset({"b"})  # type: ignore[index]
