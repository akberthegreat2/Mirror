"""Tests for executor integration with registry and components."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from mirror_core.executor import Executor, StepState
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner
from mirror_core.registry import CapabilityConfig, Registry
from mirror_core.resource import ProducerRef, ResourceEnvelope
from pydantic import BaseModel


# --- Mock models for testing ---
class MockRequest(BaseModel):
    url: str


class MockResult(BaseModel):
    content: str
    status: int = 200


# --- Real runner function (matches expected signature) ---
async def mock_runner(provider, request, settings=None, signal_bus=None, step_id=None):
    """Mock runner that calls the provider's fetch method."""
    return await provider.fetch(request)


@pytest.mark.asyncio
async def test_executor_run(monkeypatch):
    """Test that executor runs a pipeline and returns ResourceEnvelope."""
    registry = Registry()
    cap_config = CapabilityConfig(
        name="fetch",
        api_version="1.0",
        request_model=MockRequest,
        result_model=MockResult,
        runner="dummy.path",
    )
    registry.register_capability(cap_config)

    mock_provider = AsyncMock()
    mock_provider.fetch = AsyncMock(return_value=MockResult(content="hello world"))
    components = {"fetch": mock_provider}

    executor = Executor(
        registry=registry,
        components=components,
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

    async def patched_run_step(self, step_id, plan):
        step = plan.get_step(step_id)
        inputs = self._resolve_inputs(step, plan)
        provider = self._resolve_provider(step)
        request = self._build_request(step, inputs)
        result = await mock_runner(provider, request)
        envelope = ResourceEnvelope.create(
            resource_type="MockResult",
            schema_version="1.0",
            payload=result,
            producer=self._producer_ref,
            parents=[],
        )
        self._results[step_id] = envelope
        self._states[step_id] = StepState.SUCCEEDED
        await self._emit("step.succeeded", step=step, result=envelope)

    executor._run_step = patched_run_step.__get__(executor)

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

    results = await executor.execute(plan)

    assert "a" in results
    envelope = results["a"]
    assert isinstance(envelope, ResourceEnvelope)
    assert envelope.resource_type == "MockResult"
    assert envelope.payload == MockResult(content="hello world")
    assert envelope.producer.capability == "test"
    assert envelope.parents == []

    mock_provider.fetch.assert_called_once()
    call_args = mock_provider.fetch.call_args[0][0]
    assert isinstance(call_args, MockRequest)
    assert call_args.url == "https://example.com"


@pytest.mark.asyncio
async def test_executor_retry(monkeypatch):
    """Test that executor retries on failure."""
    registry = Registry()
    cap_config = CapabilityConfig(
        name="fetch",
        api_version="1.0",
        request_model=MockRequest,
        result_model=MockResult,
        runner="dummy.path",
    )
    registry.register_capability(cap_config)

    mock_provider = AsyncMock()
    call_count = 0

    async def failing_fetch(request):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ValueError("temporary failure")
        return MockResult(content="success")

    mock_provider.fetch = failing_fetch
    components = {"fetch": mock_provider}

    executor = Executor(
        registry=registry,
        components=components,
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

    async def patched_run_step(self, step_id, plan):
        step = plan.get_step(step_id)
        inputs = self._resolve_inputs(step, plan)
        provider = self._resolve_provider(step)
        request = self._build_request(step, inputs)
        result = await self._run_with_retry_and_timeout(
            step, mock_runner, provider, request, inputs
        )
        envelope = ResourceEnvelope.create(
            resource_type="MockResult",
            schema_version="1.0",
            payload=result,
            producer=self._producer_ref,
            parents=[],
        )
        self._results[step_id] = envelope
        self._states[step_id] = StepState.SUCCEEDED
        await self._emit("step.succeeded", step=step, result=envelope)

    executor._run_step = patched_run_step.__get__(executor)

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
                retry={"attempts": 3, "backoff": "fixed", "jitter": 0},
            )
        ],
        inputs={"url": "https://example.com"},
    )

    planner = Planner(registry)
    plan = planner.plan(pipeline)

    results = await executor.execute(plan)
    envelope = results["a"]
    assert envelope.payload == MockResult(content="success")
    assert call_count == 3


@pytest.mark.asyncio
async def test_executor_timeout(monkeypatch):
    """Test that executor enforces timeout."""
    registry = Registry()
    cap_config = CapabilityConfig(
        name="fetch",
        api_version="1.0",
        request_model=MockRequest,
        result_model=MockResult,
        runner="dummy.path",
    )
    registry.register_capability(cap_config)

    # Provider that hangs forever
    async def never_returns(request):
        await asyncio.Event().wait()

    mock_provider = AsyncMock()
    mock_provider.fetch = never_returns
    components = {"fetch": mock_provider}

    executor = Executor(
        registry=registry,
        components=components,
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

    async def patched_run_step(self, step_id, plan):
        step = plan.get_step(step_id)
        inputs = self._resolve_inputs(step, plan)
        provider = self._resolve_provider(step)
        request = self._build_request(step, inputs)
        try:
            await self._run_with_retry_and_timeout(step, mock_runner, provider, request, inputs)
        except Exception:
            self._states[step_id] = StepState.FAILED
            raise

    executor._run_step = patched_run_step.__get__(executor)

    pipeline = Pipeline(
        id="test",
        steps=[
            Step(
                id="a",
                capability="fetch",
                input={"url": "$pipeline.url"},
                outputs=["result"],
                timeout=0.01,
                retry={"attempts": 1},
            )
        ],
        inputs={"url": "https://example.com"},
    )

    planner = Planner(registry)
    plan = planner.plan(pipeline)

    results = await executor.execute(plan)

    assert "a" not in results
    assert executor._states.get("a") == StepState.FAILED
