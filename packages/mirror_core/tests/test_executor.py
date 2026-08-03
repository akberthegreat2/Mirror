"""Tests for executor integration with registry, components, and middleware."""

from unittest.mock import AsyncMock

import pytest
from mirror_core.executor import Executor, StepState
from mirror_core.middleware import MiddlewareChain
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner
from mirror_core.registry import CapabilityConfig, Registry
from mirror_core.resource import ProducerRef, ResourceEnvelope
from pydantic import BaseModel


class MockRequest(BaseModel):
    url: str


class MockResult(BaseModel):
    content: str
    status: int = 200


async def mock_runner(provider, request, *, signal_bus=None, step_id=None):
    """Mock runner that calls the provider's fetch method."""
    return await provider.fetch(request)


@pytest.mark.asyncio
async def test_executor_run_with_runner():
    """Executor stores result when a runner function is provided."""
    registry = Registry()
    registry.register_capability(
        CapabilityConfig(
            name="fetch",
            api_version="1.0",
            request_model=MockRequest,
            result_model=MockResult,
        )
    )

    mock_provider = AsyncMock()
    mock_provider.fetch = AsyncMock(return_value=MockResult(content="hello world"))

    executor = Executor(
        registry=registry,
        components={"fetch": mock_provider},
        max_concurrency=5,
        signal_bus=None,
        middleware_chain=None,
    )
    executor.set_producer(
        ProducerRef(
            capability="test",
            capability_version="1.0",
            provider="test",
            provider_version="1.0",
        )
    )

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
            )
        ],
        inputs={"url": "https://example.com"},
    )

    planner = Planner(registry)
    plan = planner.plan(pipeline)

    async def runner(provider, request, signal_bus=None, step_id=None):
        return await mock_runner(provider, request)

    results = await executor.execute(plan, runner=runner)

    assert "a" in results
    envelope = results["a"]
    assert isinstance(envelope, ResourceEnvelope)
    assert envelope.resource_type == "MockResult"
    assert envelope.payload == MockResult(content="hello world")
    assert envelope.producer.capability == "test"

    mock_provider.fetch.assert_called_once()
    call_args = mock_provider.fetch.call_args[0][0]
    assert isinstance(call_args, MockRequest)
    assert call_args.url == "https://example.com"


@pytest.mark.asyncio
async def test_executor_respects_step_condition():
    """Step is skipped when condition evaluates to False."""
    registry = Registry()
    registry.register_capability(
        CapabilityConfig(
            name="fetch",
            api_version="1.0",
            request_model=MockRequest,
            result_model=MockResult,
        )
    )

    executor = Executor(
        registry=registry,
        components={"fetch": AsyncMock()},
        max_concurrency=5,
    )
    executor.set_producer(
        ProducerRef(
            capability="test",
            capability_version="1.0",
            provider="test",
            provider_version="1.0",
        )
    )

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
                condition="false",
            )
        ],
        inputs={"url": "https://example.com"},
    )

    planner = Planner(registry)
    plan = planner.plan(pipeline)

    def patched_evaluate_condition(self, condition, inputs, results):
        return False

    executor._evaluate_condition = patched_evaluate_condition.__get__(executor)

    results = await executor.execute(plan, runner=AsyncMock())
    assert "a" not in results
    assert executor._states["a"] == StepState.SKIPPED


@pytest.mark.asyncio
async def test_executor_with_middleware_chain():
    """Middleware chain wraps the runner when provided."""
    registry = Registry()
    registry.register_capability(
        CapabilityConfig(
            name="fetch",
            api_version="1.0",
            request_model=MockRequest,
            result_model=MockResult,
        )
    )

    mock_provider = AsyncMock()
    mock_provider.fetch = AsyncMock(return_value=MockResult(content="ok"))

    call_order = []

    class RecordingMiddleware:
        async def __call__(self, invocation, next_middleware):
            call_order.append("before")
            result = await next_middleware(invocation)
            call_order.append("after")
            return result

    chain = MiddlewareChain([RecordingMiddleware()])

    executor = Executor(
        registry=registry,
        components={"fetch": mock_provider},
        max_concurrency=5,
        middleware_chain=chain,
    )
    executor.set_producer(
        ProducerRef(
            capability="test",
            capability_version="1.0",
            provider="test",
            provider_version="1.0",
        )
    )

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
            )
        ],
        inputs={"url": "https://example.com"},
    )

    planner = Planner(registry)
    plan = planner.plan(pipeline)

    async def runner(provider, request, signal_bus=None, step_id=None):
        return await mock_runner(provider, request)

    results = await executor.execute(plan, runner=runner)

    assert "a" in results
    assert call_order == ["before", "after"]


@pytest.mark.asyncio
async def test_executor_error_abort():
    """Step failure with on_error='abort' cancels the pipeline."""
    registry = Registry()
    registry.register_capability(
        CapabilityConfig(
            name="fetch",
            api_version="1.0",
            request_model=MockRequest,
            result_model=MockResult,
        )
    )

    mock_provider = AsyncMock()
    mock_provider.fetch = AsyncMock(side_effect=ValueError("fail"))

    executor = Executor(
        registry=registry,
        components={"fetch": mock_provider},
        max_concurrency=5,
    )
    executor.set_producer(
        ProducerRef(
            capability="test",
            capability_version="1.0",
            provider="test",
            provider_version="1.0",
        )
    )

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
                on_error="abort",
            ),
            Step(
                id="b",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
            ),
        ],
        inputs={"url": "https://example.com"},
    )

    planner = Planner(registry)
    plan = planner.plan(pipeline)

    async def runner(provider, request, signal_bus=None, step_id=None):
        return await mock_runner(provider, request)

    results = await executor.execute(plan, runner=runner)

    assert "a" not in results
    assert "b" not in results
    # The failing step should be FAILED, not CANCELLED.
    assert executor._states["a"] == StepState.FAILED
    assert executor._cancelled is True
