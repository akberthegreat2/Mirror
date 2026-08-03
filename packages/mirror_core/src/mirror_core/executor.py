"""Execution engine for DAG pipelines with concurrency, cancellation, retries, and timeout."""

from __future__ import annotations

import asyncio
import importlib
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any, cast

from pydantic import BaseModel

from mirror_core.exceptions import ExecutionError
from mirror_core.middleware import MiddlewareChain
from mirror_core.pipeline import Step
from mirror_core.planner import ExecutionPlan
from mirror_core.registry import Registry
from mirror_core.resource import ProducerRef, ResourceEnvelope

logger = logging.getLogger(__name__)


class StepState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    RETRY_WAIT = "retry_wait"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class Executor:
    """Executes pipelines with bounded concurrency and middleware chain.

    The executor does not implement retry/timeout directly; those are
    handled by the middleware chain if enabled.
    """

    def __init__(
        self,
        registry: Registry,
        components: dict[str, Any],
        max_concurrency: int = 10,
        signal_bus: Any | None = None,
        middleware_chain: MiddlewareChain | None = None,
    ):
        self.registry = registry
        self.components = components
        self.max_concurrency = max_concurrency
        self.signal_bus = signal_bus
        self.middleware_chain = middleware_chain
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._results: dict[str, ResourceEnvelope] = {}
        self._states: dict[str, StepState] = {}
        self._cancelled = False
        self._producer_ref: ProducerRef | None = None

    def set_producer(self, producer: ProducerRef) -> None:
        self._producer_ref = producer

    async def execute(
        self,
        plan: ExecutionPlan,
        runner: Callable[..., Any] | None = None,
    ) -> dict[str, ResourceEnvelope]:
        """Execute the plan.

        Args:
            plan: The execution plan.
            runner: Optional runner function (for testing). If not provided,
                    runner is resolved from capability registry.

        Returns:
            dict[str, ResourceEnvelope]: Results for each step.
        """
        self._runner = runner
        self._results = {}
        self._states = dict.fromkeys(plan.step_ids, StepState.PENDING)
        self._cancelled = False

        await self._emit("pipeline.started", plan=plan)

        for group in plan.parallel_groups:
            if self._cancelled:
                break
            ready = [
                sid
                for sid in group
                if self._states[sid] == StepState.PENDING and self._can_run(sid, plan)
            ]
            if not ready:
                continue
            tasks = [self._run_step(sid, plan) for sid in ready]
            await asyncio.gather(*tasks, return_exceptions=True)

        await self._emit("pipeline.finished", plan=plan, results=self._results)
        return self._results

    async def _run_step(self, step_id: str, plan: ExecutionPlan) -> None:
        async with self._semaphore:
            # If already in a terminal state, do nothing.
            if self._states.get(step_id) not in (StepState.PENDING, StepState.READY):
                return

            if self._cancelled:
                self._states[step_id] = StepState.CANCELLED
                return

            step = plan.get_step(step_id)
            self._states[step_id] = StepState.RUNNING
            await self._emit("step.started", step=step)

            inputs = self._resolve_inputs(step, plan)

            if step.condition and not self._evaluate_condition(
                step.condition, inputs, self._results
            ):
                self._states[step_id] = StepState.SKIPPED
                await self._emit("step.skipped", step=step)
                return

            try:
                provider = self._get_provider(step.capability)

                cap_config = self.registry.get_capability(step.capability, "1.0")
                if cap_config.request_model is None:
                    raise ExecutionError(f"No request_model for capability '{step.capability}'")
                request = cap_config.request_model.model_validate(inputs)

                if self._runner is not None:
                    runner = self._runner
                else:
                    runner = self._get_runner(step.capability)

                result = await self._execute_step_with_middleware(
                    step=step,
                    runner=runner,
                    provider=provider,
                    request=request,
                )

                if self._producer_ref is None:
                    raise ExecutionError("ProducerRef not set for executor")

                # Derive the resource type from the capability descriptor
                resource_type = (
                    cap_config.result_model.__name__
                    if cap_config.result_model
                    else f"{step.capability.capitalize()}Result"
                )

                envelope = ResourceEnvelope.create(
                    resource_type=resource_type,
                    schema_version="1.0",
                    payload=result,
                    producer=self._producer_ref,
                    parents=[r.resource_id for r in self._results.values()],
                )
                self._results[step_id] = envelope
                self._states[step_id] = StepState.SUCCEEDED
                await self._emit("step.succeeded", step=step, result=envelope)

            except Exception as e:
                self._states[step_id] = StepState.FAILED
                await self._emit("step.failed", step=step, error=str(e))
                if step.on_error == "abort":
                    self._cancelled = True
                    raise ExecutionError(f"Step {step_id} failed: {e}", cause=e) from e

    async def _execute_step_with_middleware(
        self,
        step: Step,
        runner: Callable[..., Any],
        provider: Any,
        request: Any,
    ) -> Any:
        if self.middleware_chain:
            invocation = {
                "step": step,
                "request": request,
                "provider": provider,
                "context": {
                    "signal_bus": self.signal_bus,
                    "results": self._results,
                },
            }
            return await self.middleware_chain.execute(
                invocation,
                lambda inv: runner(
                    inv["provider"],
                    inv["request"],
                    signal_bus=inv["context"]["signal_bus"],
                    step_id=inv["step"].id,
                ),
            )
        return await runner(
            provider,
            request,
            signal_bus=self.signal_bus,
            step_id=step.id,
        )

    def _get_runner(self, capability_name: str) -> Callable[..., Any]:
        cap_config = self.registry.get_capability(capability_name, "1.0")
        if cap_config.runner is None:
            raise ExecutionError(f"No runner defined for capability '{capability_name}'")
        module_path, _, func_name = cap_config.runner.rpartition(":")
        module = importlib.import_module(module_path)
        return cast(Callable[..., Any], getattr(module, func_name))

    def _get_provider(self, capability_name: str) -> Any:
        if capability_name not in self.components:
            raise ExecutionError(f"No provider for capability '{capability_name}'")
        return self.components[capability_name]

    def _resolve_inputs(self, step: Step, plan: ExecutionPlan) -> dict[str, Any]:
        inputs: dict[str, Any] = {}
        for target, source in step.input.items():
            if "." in source:
                src_step, output_name = source.split(".", 1)
                if src_step == "$pipeline":
                    inputs[target] = plan.pipeline_inputs.get(output_name)
                    continue
                envelope = self._results.get(src_step)
                if envelope is None:
                    raise ExecutionError(f"Missing dependency: {src_step} -> {step.id}")
                payload = envelope.payload
                if isinstance(payload, BaseModel):
                    inputs[target] = getattr(payload, output_name, None)
                elif isinstance(payload, dict):
                    inputs[target] = payload.get(output_name)
                else:
                    inputs[target] = None
            else:
                inputs[target] = source
        return inputs

    def _can_run(self, step_id: str, plan: ExecutionPlan) -> bool:
        deps = plan.dependencies.get(step_id, set())
        for dep in deps:
            if dep == "$pipeline":
                continue
            if self._states.get(dep) not in (StepState.SUCCEEDED, StepState.SKIPPED):
                return False
        return True

    def _evaluate_condition(
        self, condition: str, inputs: dict[str, Any], results: dict[str, Any]
    ) -> bool:
        return True

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        if self.signal_bus:
            await self.signal_bus.emit(signal, **kwargs)

    def cancel(self) -> None:
        self._cancelled = True
