"""Tests for executor."""

import pytest
from mirror_core.executor import Executor
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner
from mirror_core.registry import CapabilityConfig, Registry
from mirror_core.resource import ProducerRef


@pytest.mark.asyncio
async def test_executor_run():
    r = Registry()
    r.register_capability(CapabilityConfig(name="fetch", api_version="1.0"))

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(id="a", capability="fetch", input={"source": "$pipeline.url"}, outputs=["result"]),
        ],
    )
    p = Planner(r)
    plan = p.plan(pipeline)

    executor = Executor()
    executor.set_producer(
        ProducerRef(
            capability="test", capability_version="1.0", provider="test", provider_version="1.0"
        )
    )

    async def runner(step: Step, inputs: dict) -> dict:
        return {"content": "ok"}

    results = await executor.execute(plan, runner)
    assert "a" in results
    assert results["a"].payload == {"content": "ok"}
    assert results["a"].producer.capability == "test"
