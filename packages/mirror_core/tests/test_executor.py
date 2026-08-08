"""Tests for isolated execution runs and terminal outcomes."""

from unittest.mock import AsyncMock

import pytest
from mirror_core.exceptions import ExecutionError
from mirror_core.executor import Executor, RunOutcome, StepState
from mirror_core.extensions.models import CapabilityManifest, ProviderManifest
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.middleware import MiddlewareChain, MiddlewareInvocation
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner
from pydantic import BaseModel


class MockRequest(BaseModel):
    url: str


class MockResult(BaseModel):
    content: str
    status: int = 200


def make_plan(*steps: Step):
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="fetch",
            api_version="1.2",
            request_model=MockRequest,
            result_model=MockResult,
            output_ports={"result": MockResult},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="httpx",
            capability="fetch",
            capability_api="~=1.0",
            factory="test:provider",
            metadata={"version": "0.9"},
        )
    )
    pipeline = Pipeline(
        id="test",
        steps=list(steps),
        inputs={"url": "str"},
    )
    return Planner(registry, default_providers={"fetch": "httpx"}).plan(pipeline)


async def runner(provider, request, runner_context=None):
    return await provider.fetch(request)


@pytest.mark.asyncio
async def test_executor_uses_runtime_inputs_and_accurate_producer() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(return_value=MockResult(content="hello"))
    plan = make_plan(
        Step(
            id="fetch_page",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    )
    executor = Executor({("fetch", "httpx"): provider})

    result = await executor.execute_run(
        plan,
        inputs={"url": "https://example.com"},
        runner=runner,
    )

    assert result.outcome is RunOutcome.SUCCEEDED
    envelope = result.results["fetch_page"]
    assert envelope.producer.capability == "fetch"
    assert envelope.producer.capability_version == "1.2"
    assert envelope.producer.provider == "httpx"
    assert envelope.producer.step_id == "fetch_page"
    assert envelope.parents == ()
    provider.fetch.assert_awaited_once_with(MockRequest(url="https://example.com"))


@pytest.mark.asyncio
async def test_executor_does_not_force_keyword_arguments() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(return_value=MockResult(content="hello"))
    plan = make_plan(
        Step(
            id="fetch_page",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        ),
    )
    executor = Executor({("fetch", "httpx"): provider})

    result = await executor.execute_run(
        plan,
        inputs={"url": "https://example.com"},
        runner=runner,
    )

    assert result.outcome is RunOutcome.SUCCEEDED
    provider.fetch.assert_awaited_once_with(MockRequest(url="https://example.com"))


@pytest.mark.asyncio
async def test_executor_tracks_only_direct_resource_parents() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(side_effect=[MockResult(content="a"), MockResult(content="b")])
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        ),
        Step(id="b", capability="fetch", input={"url": "a.content"}, outputs=["result"]),
    )
    executor = Executor({("fetch", "httpx"): provider}, max_concurrency=1)

    result = await executor.execute_run(plan, inputs={"url": "https://example.com"}, runner=runner)

    assert result.results["b"].parents == (result.results["a"].resource_id,)


@pytest.mark.asyncio
async def test_executor_condition_can_skip_step() -> None:
    provider = AsyncMock()
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
            condition="false",
        )
    )
    executor = Executor({("fetch", "httpx"): provider})

    result = await executor.execute_run(plan, inputs={"url": "x"}, runner=runner)

    assert result.states["a"] is StepState.SKIPPED
    assert result.outcome is RunOutcome.SUCCEEDED
    provider.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_executor_abort_is_reported_and_raised() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(side_effect=ValueError("network failed"))
    plan = make_plan(
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
            input={"url": "a.content"},
            outputs=["result"],
        ),
    )
    executor = Executor({("fetch", "httpx"): provider})

    with pytest.raises(ExecutionError, match="network failed"):
        await executor.execute(plan, inputs={"url": "x"}, runner=runner)

    assert executor.last_run is not None
    assert executor.last_run.outcome is RunOutcome.FAILED
    assert executor.last_run.states["a"] is StepState.FAILED
    assert executor.last_run.states["b"] in {StepState.CANCELLED, StepState.SKIPPED}


@pytest.mark.asyncio
async def test_middleware_can_short_circuit_provider() -> None:
    provider = AsyncMock()

    class CacheMiddleware:
        async def __call__(self, invocation: MiddlewareInvocation, next_middleware):
            return MockResult(content="cached")

    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    )
    executor = Executor(
        {("fetch", "httpx"): provider},
        middleware_chain=MiddlewareChain([CacheMiddleware()]),
    )

    result = await executor.execute_run(plan, inputs={"url": "x"}, runner=runner)

    assert result.results["a"].payload == MockResult(content="cached")
    provider.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_concurrent_runs_do_not_share_state() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(side_effect=lambda request: MockResult(content=request.url))
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    )
    executor = Executor({("fetch", "httpx"): provider})

    first, second = await __import__("asyncio").gather(
        executor.execute_run(plan, inputs={"url": "one"}, runner=runner),
        executor.execute_run(plan, inputs={"url": "two"}, runner=runner),
    )

    assert first.run_id != second.run_id
    assert first.results["a"].payload.content == "one"
    assert second.results["a"].payload.content == "two"


@pytest.mark.asyncio
async def test_step_retry_policy_is_enforced() -> None:
    from mirror_core.pipeline import RetryPolicy

    provider = AsyncMock()
    provider.fetch = AsyncMock(side_effect=[ValueError("temporary"), MockResult(content="recovered")])
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
            retry=RetryPolicy(attempts=2),
        )
    )
    executor = Executor({("fetch", "httpx"): provider})

    result = await executor.execute_run(plan, inputs={"url": "x"}, runner=runner)

    assert result.outcome is RunOutcome.SUCCEEDED
    assert provider.fetch.await_count == 2


@pytest.mark.asyncio
async def test_step_timeout_is_enforced() -> None:
    import asyncio

    provider = AsyncMock()

    async def slow_fetch(request: MockRequest) -> MockResult:
        await asyncio.sleep(1)
        return MockResult(content="late")

    provider.fetch = slow_fetch
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
            timeout=0.01,
        )
    )
    executor = Executor({("fetch", "httpx"): provider})

    result = await executor.execute_run(plan, inputs={"url": "x"}, runner=runner)

    assert result.outcome is RunOutcome.FAILED
    assert result.states["a"] is StepState.FAILED


@pytest.mark.asyncio
async def test_cancel_stops_a_running_task() -> None:
    import asyncio

    started = asyncio.Event()
    cancelled = asyncio.Event()
    provider = AsyncMock()

    async def blocking_fetch(request: MockRequest) -> MockResult:
        started.set()
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            cancelled.set()
            raise
        return MockResult(content="never")

    provider.fetch = blocking_fetch
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    )
    executor = Executor({("fetch", "httpx"): provider})
    task = asyncio.create_task(executor.execute_run(plan, inputs={"url": "x"}, runner=runner))
    await started.wait()
    run_id = next(iter(executor._active_runs))
    executor.cancel(run_id)
    result = await task

    assert cancelled.is_set()
    assert result.outcome is RunOutcome.CANCELLED
    assert result.states["a"] is StepState.CANCELLED


@pytest.mark.asyncio
async def test_abort_after_prior_success_is_partially_succeeded() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(side_effect=[MockResult(content="ok"), ValueError("boom")])
    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        ),
        Step(
            id="b",
            capability="fetch",
            input={"url": "a.content"},
            outputs=["result"],
            on_error="abort",
        ),
    )
    executor = Executor({("fetch", "httpx"): provider})

    result = await executor.execute_run(plan, inputs={"url": "x"}, runner=runner)

    assert result.outcome is RunOutcome.PARTIALLY_SUCCEEDED
    assert result.states["a"] is StepState.SUCCEEDED
    assert result.states["b"] is StepState.FAILED


@pytest.mark.asyncio
async def test_resume_rejects_unknown_checkpoint_steps() -> None:
    from mirror_core.workers import InMemoryCheckpointStore

    plan = make_plan(
        Step(
            id="a",
            capability="fetch",
            input={"url": "$pipeline.url"},
            outputs=["result"],
        )
    )
    checkpoint = InMemoryCheckpointStore()
    run_id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000999")
    checkpoint.save(
        run_id,
        "a",
        {
            "run_id": str(run_id),
            "pipeline_id": plan.pipeline_id,
            "step_id": "a",
            "states": {"ghost": "running"},
            "results": {},
            "errors": {},
            "retry_counts": {},
            "failed_step_id": None,
            "cancelled": False,
            "inputs": {"url": "x"},
        },
    )
    executor = Executor({("fetch", "httpx"): AsyncMock()}, checkpoint_store=checkpoint)

    with pytest.raises(ExecutionError, match="unknown step ids"):
        await executor.resume_from_checkpoint(plan, run_id=run_id, inputs={"url": "x"}, runner=runner)
