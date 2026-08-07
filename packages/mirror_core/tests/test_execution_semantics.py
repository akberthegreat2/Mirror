"""Tests for the ADR-0025 runtime context and policy contracts."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mirror_core.execution import CapabilityContext, ExecutionContext, ExecutionPolicy
from mirror_core.executor import Executor, RunOutcome
from mirror_core.extensions.models import CapabilityManifest, ProviderManifest
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.metadata import InMemoryMetadataStore, MetadataNamespaces
from mirror_core.pipeline import CompensationPolicy, FallbackPolicy, Pipeline, Step
from mirror_core.planner import Planner
from mirror_core.resource import ProducerRef, ResourceEnvelope
from mirror_core.workers import InMemoryCheckpointStore, InMemoryDeadLetterQueue
from pydantic import BaseModel


class Request(BaseModel):
    url: str


class Result(BaseModel):
    content: str


def _plan() -> tuple[Executor, object]:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="fetch",
            api_version="1.0",
            request_model=Request,
            result_model=Result,
            output_ports={"result": Result},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="httpx",
            capability="fetch",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    pipeline = Pipeline(
        id="runtime",
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
    plan = Planner(registry, default_providers={"fetch": "httpx"}).plan(pipeline)
    executor = Executor({("fetch", "httpx"): AsyncMock()})
    return executor, plan


@pytest.mark.asyncio
async def test_executor_passes_runtime_contexts_to_runners() -> None:
    provider = AsyncMock()
    provider.fetch = AsyncMock(return_value=Result(content="ok"))
    executor, plan = _plan()
    executor.components = {("fetch", "httpx"): provider}

    seen: dict[str, object] = {}

    async def runner(provider, request, runner_context=None):
        seen["execution_context"] = (
            runner_context.execution_context if runner_context else None
        )
        seen["capability_context"] = (
            runner_context.capability_context if runner_context else None
        )
        seen["middleware_context"] = (
            runner_context.middleware_context if runner_context else None
        )
        seen["signal_bus"] = runner_context.signal_bus if runner_context else None
        seen["step_id"] = runner_context.step_id if runner_context else None
        return await provider.fetch(request)

    result = await executor.execute_run(
        plan, inputs={"url": "https://example.com"}, runner=runner
    )

    assert result.outcome is RunOutcome.SUCCEEDED
    execution_context = seen["execution_context"]
    capability_context = seen["capability_context"]
    middleware_context = seen["middleware_context"]
    assert isinstance(execution_context, ExecutionContext)
    assert isinstance(capability_context, CapabilityContext)
    assert middleware_context.step_id == "fetch"
    assert capability_context.execution is execution_context
    assert capability_context.step_id == "fetch"
    assert capability_context.provider == "httpx"
    assert capability_context.policy.on_error == "abort"
    assert seen["step_id"] == "fetch"
    assert seen["signal_bus"] is executor.signal_bus


def test_execution_context_is_immutable_snapshot() -> None:
    execution = ExecutionContext(
        run_id=__import__("uuid").uuid4(),
        pipeline_id="demo",
        inputs={"url": "https://example.com"},
        results={},
        metadata={"source": "test"},
    )

    with pytest.raises(TypeError):
        execution.inputs["url"] = "changed"  # type: ignore[index]

    assert execution.metadata["source"] == "test"


def test_capability_context_uses_explicit_execution_policy() -> None:
    execution = ExecutionContext(
        run_id=__import__("uuid").uuid4(),
        pipeline_id="demo",
    )
    policy = ExecutionPolicy(on_error="continue")
    context = CapabilityContext.from_execution(
        execution,
        step_id="step-1",
        capability="fetch",
        capability_version="1.0",
        provider="httpx",
        provider_version="1.0",
        policy=policy,
        metadata={"provider": "httpx"},
    )

    assert context.execution is execution
    assert context.policy == policy
    assert context.metadata["provider"] == "httpx"


def test_resource_envelope_deep_copies_payload() -> None:
    payload = Result(content="before")
    envelope = ResourceEnvelope.create(
        resource_type="Result",
        schema_version="1.0",
        payload=payload,
        producer=ProducerRef(
            capability="fetch",
            capability_version="1.0",
            provider="httpx",
        ),
    )

    payload.content = "after"
    assert envelope.payload.content == "before"


class Payload(BaseModel):
    value: int


@pytest.mark.asyncio
async def test_executor_records_checkpoint_and_dead_letter() -> None:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="demo",
            api_version="1.0",
            request_model=Payload,
            result_model=Payload,
            output_ports={"result": Payload},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="ok",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="boom",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    pipeline = Pipeline(
        id="runtime",
        inputs={"value": "int"},
        steps=[
            Step(
                id="first",
                capability="demo",
                provider="ok",
                input={"value": "$pipeline.value"},
                outputs=["result"],
            ),
            Step(
                id="second",
                capability="demo",
                provider="boom",
                input={"value": "first.value"},
                outputs=["result"],
            ),
        ],
    )
    plan = Planner(registry).plan(pipeline)
    checkpoint_store = InMemoryCheckpointStore()
    dead_letters = InMemoryDeadLetterQueue()
    executor = Executor(
        {
            ("demo", "ok"): AsyncMock(run=AsyncMock(return_value=Payload(value=1))),
            ("demo", "boom"): AsyncMock(
                run=AsyncMock(side_effect=RuntimeError("boom"))
            ),
        },
        checkpoint_store=checkpoint_store,
        dead_letter_queue=dead_letters,
    )

    async def runner(provider, request, **kwargs):
        return await provider.run(request)

    result = await executor.execute_run(plan, inputs={"value": 1}, runner=runner)

    assert result.outcome is RunOutcome.PARTIALLY_SUCCEEDED
    checkpoint = checkpoint_store.load(result.run_id, "first")
    assert checkpoint is not None
    assert checkpoint["step_id"] == "first"
    record = dead_letters.get(result.run_id)
    assert record is not None
    assert record.step_id == "second"
    assert record.terminal_status == "partially_succeeded"


class PrimaryProvider:
    async def run(self, request: Request) -> Result:
        raise RuntimeError("primary failed")


class FallbackProvider:
    async def run(self, request: Request) -> Result:
        return Result(content=f"fallback:{request.url}")


@pytest.mark.asyncio
async def test_executor_uses_fallback_provider_when_primary_fails() -> None:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="fetch",
            api_version="1.0",
            request_model=Request,
            result_model=Result,
            output_ports={"result": Result},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="primary",
            capability="fetch",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="fallback",
            capability="fetch",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    pipeline = Pipeline(
        id="fallback",
        inputs={"url": "str"},
        steps=[
            Step(
                id="fetch",
                capability="fetch",
                provider="primary",
                input={"url": "$pipeline.url"},
                outputs=["result"],
                fallback=FallbackPolicy(providers=("fallback",)),
                on_error="fallback",
            )
        ],
    )
    plan = Planner(registry).plan(pipeline)
    executor = Executor(
        {
            ("fetch", "primary"): PrimaryProvider(),
            ("fetch", "fallback"): FallbackProvider(),
        }
    )

    async def runner(provider, request, **kwargs):
        return await provider.run(request)

    result = await executor.execute_run(
        plan, inputs={"url": "https://example.com"}, runner=runner
    )

    assert result.outcome is RunOutcome.SUCCEEDED
    envelope = result.results["fetch"]
    assert envelope.producer.provider == "fallback"
    assert envelope.payload.content == "fallback:https://example.com"


class TransientProvider:
    def __init__(self) -> None:
        self.calls = 0

    async def run(self, request: Payload) -> Payload:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient failure")
        return Payload(value=request.value + 1)


@pytest.mark.asyncio
async def test_executor_records_metadata_and_triggers_compensation() -> None:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="demo",
            api_version="1.0",
            request_model=Request,
            result_model=Result,
            output_ports={"result": Result},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="boom",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    pipeline = Pipeline(
        id="compensation",
        inputs={"url": "str"},
        steps=[
            Step(
                id="primary",
                capability="demo",
                provider="boom",
                input={"url": "$pipeline.url"},
                outputs=["result"],
                compensation=CompensationPolicy(steps=("cleanup",)),
                on_error="abort",
            )
        ],
    )
    plan = Planner(registry).plan(pipeline)
    metadata_store = InMemoryMetadataStore()
    compensation_handler = AsyncMock()

    class BoomProvider:
        async def run(self, request: Request) -> Result:
            raise RuntimeError("boom")

    executor = Executor(
        {("demo", "boom"): BoomProvider()},
        metadata_store=metadata_store,
        compensation_handler=compensation_handler,
    )

    async def runner(provider, request, **kwargs):
        return await provider.run(request)

    result = await executor.execute_run(
        plan, inputs={"url": "https://example.com"}, runner=runner
    )

    assert result.outcome is RunOutcome.FAILED
    compensation_handler.assert_awaited_once()
    assert (
        metadata_store.get(MetadataNamespaces.EXECUTION_RUNS, str(result.run_id))
        is not None
    )
    step_record = metadata_store.get(
        MetadataNamespaces.STEP_RUNS, f"{result.run_id}:primary"
    )
    assert step_record is not None
    assert step_record.payload["state"] == RunOutcome.FAILED.value
    audit_record = metadata_store.get(
        MetadataNamespaces.AUDIT_EVENTS, f"{result.run_id}:compensation.triggered"
    )
    assert audit_record is not None
    terminal_record = metadata_store.get(
        MetadataNamespaces.TERMINAL_OUTCOMES, str(result.run_id)
    )
    assert terminal_record is not None
    assert terminal_record.payload["outcome"] == RunOutcome.FAILED.value


@pytest.mark.asyncio
async def test_executor_can_resume_from_checkpoint() -> None:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="demo",
            api_version="1.0",
            request_model=Payload,
            result_model=Payload,
            output_ports={"result": Payload},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="first",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="second",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    pipeline = Pipeline(
        id="resume",
        inputs={"value": "int"},
        steps=[
            Step(
                id="first",
                capability="demo",
                provider="first",
                input={"value": "$pipeline.value"},
                outputs=["result", "value"],
            ),
            Step(
                id="second",
                capability="demo",
                provider="second",
                input={"value": "first.value"},
                outputs=["result", "value"],
            ),
        ],
    )
    plan = Planner(registry).plan(pipeline)
    checkpoint_store = InMemoryCheckpointStore()
    executor = Executor(
        {
            ("demo", "first"): AsyncMock(run=AsyncMock(return_value=Payload(value=1))),
            ("demo", "second"): TransientProvider(),
        },
        checkpoint_store=checkpoint_store,
    )

    async def runner(provider, request, **kwargs):
        return await provider.run(request)

    failed = await executor.execute_run(plan, inputs={"value": 0}, runner=runner)
    assert failed.outcome is RunOutcome.PARTIALLY_SUCCEEDED
    latest = checkpoint_store.latest(failed.run_id)
    assert latest is not None
    assert latest[0] == "first"

    resumed = await executor.resume_from_checkpoint(
        plan, run_id=failed.run_id, runner=runner
    )
    assert resumed.run_id == failed.run_id
    assert resumed.outcome is RunOutcome.SUCCEEDED
    assert resumed.results["second"].payload.value == 2


@pytest.mark.asyncio
async def test_executor_replays_dead_letter_from_checkpoint() -> None:
    registry = ExtensionRegistryManager()
    registry.register_capability(
        CapabilityManifest(
            name="demo",
            api_version="1.0",
            request_model=Payload,
            result_model=Payload,
            output_ports={"result": Payload},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="first",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    registry.register_provider(
        ProviderManifest(
            name="second",
            capability="demo",
            capability_api="~=1.0",
            factory="tests:test",
            metadata={"version": "1.0"},
        )
    )
    pipeline = Pipeline(
        id="replay",
        inputs={"value": "int"},
        steps=[
            Step(
                id="first",
                capability="demo",
                provider="first",
                input={"value": "$pipeline.value"},
                outputs=["result", "value"],
            ),
            Step(
                id="second",
                capability="demo",
                provider="second",
                input={"value": "first.value"},
                outputs=["result", "value"],
            ),
        ],
    )
    plan = Planner(registry).plan(pipeline)
    checkpoint_store = InMemoryCheckpointStore()
    dead_letters = InMemoryDeadLetterQueue()
    second = TransientProvider()
    executor = Executor(
        {
            ("demo", "first"): AsyncMock(run=AsyncMock(return_value=Payload(value=1))),
            ("demo", "second"): second,
        },
        checkpoint_store=checkpoint_store,
        dead_letter_queue=dead_letters,
    )

    async def runner(provider, request, **kwargs):
        return await provider.run(request)

    failed = await executor.execute_run(plan, inputs={"value": 0}, runner=runner)
    assert failed.outcome is RunOutcome.PARTIALLY_SUCCEEDED
    assert dead_letters.get(failed.run_id) is not None

    replayed = await executor.replay_dead_letter(
        plan, run_id=failed.run_id, runner=runner
    )
    assert replayed.run_id == failed.run_id
    assert replayed.outcome is RunOutcome.SUCCEEDED
    assert dead_letters.get(failed.run_id) is None
