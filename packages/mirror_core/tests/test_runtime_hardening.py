"""Additional ADR-0025 hardening tests for runtime invariants."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import uuid4

import pytest
from mirror_core.execution import CapabilityContext, ExecutionContext, ExecutionPolicy
from mirror_core.middleware import MiddlewareChain, MiddlewareInvocation
from mirror_core.resource import ProducerRef, ResourceEnvelope
from mirror_core.signals import SignalBus
from pydantic import BaseModel, ValidationError


class Payload(BaseModel):
    """Simple payload used for immutable runtime snapshots."""

    value: int


@pytest.mark.asyncio
async def test_middleware_chain_executes_in_declaration_order() -> None:
    """Middleware should run in the order it was declared."""

    seen: list[str] = []

    class FirstMiddleware:
        async def __call__(
            self,
            invocation: MiddlewareInvocation,
            next_middleware: Callable[[MiddlewareInvocation], Awaitable[BaseModel]],
        ) -> BaseModel:
            seen.append("first-before")
            result = await next_middleware(invocation)
            seen.append("first-after")
            return result

    class SecondMiddleware:
        async def __call__(
            self,
            invocation: MiddlewareInvocation,
            next_middleware: Callable[[MiddlewareInvocation], Awaitable[BaseModel]],
        ) -> BaseModel:
            seen.append("second-before")
            result = await next_middleware(invocation)
            seen.append("second-after")
            return result

    invocation = MiddlewareInvocation.model_construct(
        step=object(),
        request=object(),
        provider=object(),
        execution_context=ExecutionContext(
            run_id=uuid4(),
            pipeline_id="demo",
        ),
        capability_context=CapabilityContext.from_execution(
            ExecutionContext(
                run_id=uuid4(),
                pipeline_id="demo",
            ),
            step_id="step-1",
            capability="demo",
            capability_version="1.0",
            provider="provider",
        ),
        context={},
        middleware_context=None,
    )

    async def final(_: MiddlewareInvocation) -> BaseModel:
        seen.append("final")
        return Payload(value=1)

    result = await MiddlewareChain([FirstMiddleware(), SecondMiddleware()]).execute(
        invocation,
        final,
    )

    assert result == Payload(value=1)
    assert seen == [
        "first-before",
        "second-before",
        "final",
        "second-after",
        "first-after",
    ]


@pytest.mark.asyncio
async def test_signal_bus_emits_receivers_in_subscription_order() -> None:
    """Signal receivers should run in the order they were subscribed."""

    bus = SignalBus()
    seen: list[str] = []

    def first(*args: object, **kwargs: object) -> None:
        seen.append("first")

    async def second(*args: object, **kwargs: object) -> None:
        seen.append("second")

    bus.subscribe("demo.started", first)
    bus.subscribe("demo.started", second)

    await bus.emit("demo.started")

    assert seen == ["first", "second"]


def test_execution_context_snapshots_remain_read_only() -> None:
    """ExecutionContext should expose read-only mapping snapshots."""

    execution = ExecutionContext(
        run_id=uuid4(),
        pipeline_id="demo",
        inputs={"url": "https://example.com"},
        results={
            "existing": ResourceEnvelope.create(
                resource_type="Payload",
                schema_version="1.0",
                payload=Payload(value=1),
                producer=ProducerRef(
                    capability="demo",
                    capability_version="1.0",
                    provider="provider",
                ),
            )
        },
        metadata={"source": "test"},
    )

    with pytest.raises(TypeError):
        execution.inputs["url"] = "changed"  # type: ignore[index]

    with pytest.raises(TypeError):
        execution.results["other"] = execution.results["existing"]  # type: ignore[index]

    with pytest.raises(TypeError):
        execution.metadata["source"] = "changed"  # type: ignore[index]


def test_capability_context_snapshots_remain_read_only() -> None:
    """CapabilityContext should also expose read-only metadata."""

    execution = ExecutionContext(run_id=uuid4(), pipeline_id="demo")
    context = CapabilityContext.from_execution(
        execution,
        step_id="step-1",
        capability="demo",
        capability_version="1.0",
        provider="provider",
        metadata={"provider": "provider"},
        policy=ExecutionPolicy(on_error="continue"),
    )

    with pytest.raises(TypeError):
        context.metadata["provider"] = "other"  # type: ignore[index]

    assert context.policy.on_error == "continue"


def test_resource_envelope_snapshots_remain_read_only() -> None:
    """ResourceEnvelope should freeze provenance and metadata snapshots."""

    envelope = ResourceEnvelope.create(
        resource_type="Payload",
        schema_version="1.0",
        payload=Payload(value=1),
        producer=ProducerRef(
            capability="demo",
            capability_version="1.0",
            provider="provider",
        ),
        parents=[uuid4()],
        metadata={"source": "test"},
    )

    with pytest.raises(TypeError):
        envelope.metadata["source"] = "changed"  # type: ignore[index]

    with pytest.raises(ValidationError):
        envelope.parents += (uuid4(),)  # type: ignore[operator]
