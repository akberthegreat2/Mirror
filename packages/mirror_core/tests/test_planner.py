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
            Step(id="b", capability="archive", input={"resource": "a.result"}, outputs=["result"]),
            Step(id="c", capability="archive", input={"resource": "b.result"}, outputs=[]),
        ],
        inputs={"url": "https://example.com"},
    )

    p = Planner(r)
    plan = p.plan(pipeline)
    order = plan.order
    assert order.index("a") < order.index("b") < order.index("c")


def test_planner_cycle():
    r = Registry()
    r.register_capability(CapabilityConfig(name="fetch", api_version="1.0"))
    r.register_capability(CapabilityConfig(name="archive", api_version="1.0"))

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
