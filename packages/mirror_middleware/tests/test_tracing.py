"""Tests for tracing middleware."""

import pytest
from pydantic import BaseModel

from mirror_core.middleware import Invocation
from mirror_core.pipeline import Step
from mirror_middleware.tracing import TracingMiddleware


class TracingRequest(BaseModel):
    url: str


@pytest.mark.asyncio
async def test_tracing_propagates_context():
    async def mock_next(invocation):
        return invocation.context

    middleware = TracingMiddleware(service_name="mirror-test")
    invocation = Invocation(
        step=Step(id="trace-step", capability="fetch"),
        request=TracingRequest(url="https://example.com"),
        provider=object(),
        context={"run_id": "run-1"},
    )

    context = await middleware(invocation, mock_next)
    assert context["trace"]["service_name"] == "mirror-test"
    assert context["trace"]["step_id"] == "trace-step"
    assert context["trace"]["run_id"] == "run-1"
