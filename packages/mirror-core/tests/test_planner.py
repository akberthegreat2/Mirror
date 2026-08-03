"""Tests for planner."""

import pytest
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner, PlannerError
from mirror_core.registry import CapabilityConfig, Registry


def test_planner_cycle_detection():
    r = Registry()
    r.register_capability(CapabilityConfig(name="fetch", api_version="1.0"))
    r.register_capability(CapabilityConfig(name="archive", api_version="1.0"))

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(id="a", capability="fetch", input={"source": "$pipeline.url"}, outputs=["result"]),
            Step(id="b", capability="archive", input={"resource": "a.result"}, outputs=[]),
            Step(id="c", capability="archive", input={"resource": "b.result"}, outputs=[]),
        ],
    )
    # No cycle
    p = Planner(r)
    plan = p.plan(pipeline)
    assert plan.order == ["a", "b", "c"] or plan.order == ["a", "b", "c"]  # exact order may vary


def test_planner_cycle():
    r = Registry()
    r.register_capability(CapabilityConfig(name="fetch", api_version="1.0"))
    r.register_capability(CapabilityConfig(name="archive", api_version="1.0"))

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(id="a", capability="fetch", input={"source": "$pipeline.url"}, outputs=["result"]),
            Step(id="b", capability="archive", input={"resource": "a.result"}, outputs=[]),
        ],
    )
    # Introduce cycle by making b depend on a and a depend on b (not possible with simple inputs)
    # We'll create a cycle via mutual references in inputs
    pipeline = Pipeline(
        id="test",
        steps=[
            Step(id="a", capability="fetch", input={"source": "b.result"}, outputs=["result"]),
            Step(id="b", capability="archive", input={"resource": "a.result"}, outputs=["result"]),
        ],
    )
    p = Planner(r)
    with pytest.raises(PlannerError):
        p.plan(pipeline)
