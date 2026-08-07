"""Tests for the trusted pipeline compiler."""

from __future__ import annotations

import pytest
from mirror_core.compiler import PipelineCompiler
from mirror_core.exceptions import PlannerError
from mirror_core.extensions.models import CapabilityManifest, ProviderManifest
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.pipeline import Pipeline, Step
from pydantic import BaseModel


class Request(BaseModel):
    """Simple request model used by the compiler tests."""

    url: str


class Result(BaseModel):
    """Simple result model used by the compiler tests."""

    content: str


def _registry() -> ExtensionRegistryManager:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="fetch",
            api_version="1.0",
            request_model=Request,
            result_model=Result,
            input_ports={"url": Request},
            output_ports={"result": Result},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="httpx",
            capability="fetch",
            capability_api="~=1.0",
            factory="tests:test",
        )
    )
    return registry


def test_pipeline_compiler_accepts_raw_pipeline_definition() -> None:
    """The compiler should validate raw mappings before planning."""

    compiler = PipelineCompiler(_registry(), default_providers={"fetch": "httpx"})
    plan = compiler.compile(
        {
            "id": "trusted",
            "inputs": {"url": "str"},
            "steps": [
                {
                    "id": "fetch",
                    "capability": "fetch",
                    "input": {"url": "$pipeline.url"},
                    "outputs": ["result"],
                }
            ],
        }
    )

    assert plan.pipeline_id == "trusted"
    assert plan.order == ("fetch",)
    assert plan.input_names == frozenset({"url"})
    assert plan.get_step("fetch").provider.name == "httpx"


def test_pipeline_compiler_is_deterministic() -> None:
    """Repeated compilation should produce the same immutable plan."""

    compiler = PipelineCompiler(_registry(), default_providers={"fetch": "httpx"})
    pipeline = Pipeline(
        id="trusted",
        inputs={"url": "str"},
        steps=[
            Step(
                id="fetch",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
            )
        ],
    )

    first = compiler.compile(pipeline)
    second = compiler.compile(pipeline.model_dump(mode="python"))

    assert first.to_dict() == second.to_dict()
    assert first.config_fingerprint == second.config_fingerprint


def test_pipeline_compiler_reports_schema_errors() -> None:
    """Schema errors should fail at compilation time, not at execution time."""

    compiler = PipelineCompiler(_registry(), default_providers={"fetch": "httpx"})

    with pytest.raises(PlannerError, match="Invalid pipeline definition"):
        compiler.compile({"steps": []})
