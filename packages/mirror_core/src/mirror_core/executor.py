"""Execution engine for DAG pipelines with concurrency, cancellation, retries, and timeout."""

from __future__ import annotations

import asyncio
import importlib
import logging
import random
from collections.abc import Callable
from enum import Enum
from typing import Any

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
    """Executes pipelines with bounded concurrency, retries, timeouts, and state management."""

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

    async def execute(self, plan: ExecutionPlan) -> dict[str, ResourceEnvelope]:
        self._results = {}
        self._states = {step_id: StepState.PENDING for step_id in plan.step_ids}
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
                provider = self._resolve_provider(step)
                request = self._build_request(step, inputs)
                cap_config = self.registry.get_capability(step.capability, "1.0")
                runner_path = cap_config.runner
                if not runner_path:
                    raise ExecutionError(f"No runner defined for capability '{step.capability}'")
                module_path, _, func_name = runner_path.rpartition(":")
                module = importlib.import_module(module_path)
                runner_func = getattr(module, func_name)
            except Exception as e:
                self._states[step_id] = StepState.FAILED
                await self._emit("step.failed", step=step, error=str(e))
                if step.on_error == "abort":
                    self._cancelled = True
                    raise ExecutionError(f"Step {step_id} setup failed: {e}", cause=e) from e
                return

            try:
                result = await self._run_with_retry_and_timeout(
                    step, runner_func, provider, request, inputs
                )
            except Exception as e:
                self._states[step_id] = StepState.FAILED
                await self._emit("step.failed", step=step, error=str(e))
                if step.on_error == "abort":
                    self._cancelled = True
                    raise ExecutionError(f"Step {step_id} failed: {e}", cause=e) from e
                return

            if self._producer_ref is None:
                raise ExecutionError("ProducerRef not set for executor")

            if not isinstance(result, BaseModel):
                raise ExecutionError(
                    f"Step {step_id} returned non-BaseModel output: {type(result).__name__}"
                )

            cap_config = self.registry.get_capability(step.capability, "1.0")
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

    async def _run_with_retry_and_timeout(
        self,
        step: Step,
        runner: Callable[..., Any],
        provider: Any,
        request: BaseModel,
        inputs: dict[str, Any],
    ) -> Any:
        retry_config = step.retry or {}
        attempts = retry_config.get("attempts", 1)
        backoff = retry_config.get("backoff", "fixed")
        jitter = retry_config.get("jitter", 0.0)
        timeout = step.timeout

        last_exception: Exception | None = None

        for attempt in range(attempts):
            try:
                if attempt > 0:
                    await self._emit("step.retrying", step=step, attempt=attempt + 1)
                    wait = self._calculate_backoff(attempt, backoff, jitter)
                    await asyncio.sleep(wait)

                if timeout is not None and timeout > 0:
                    result = await asyncio.wait_for(
                        runner(
                            provider,
                            request,
                            settings=None,
                            signal_bus=self.signal_bus,
                            step_id=step.id,
                        ),
                        timeout=timeout,
                    )
                else:
                    result = await runner(
                        provider,
                        request,
                        settings=None,
                        signal_bus=self.signal_bus,
                        step_id=step.id,
                    )
                return result

            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt == attempts - 1:
                    raise ExecutionError(f"Step {step.id} timed out after {timeout}s") from e
                continue
            except Exception as e:
                last_exception = e
                if attempt == attempts - 1:
                    raise
                continue

        raise ExecutionError(
            f"Step {step.id} failed after {attempts} attempts", cause=last_exception
        )

    def _calculate_backoff(self, attempt: int, backoff: str, jitter: float) -> float:
        if backoff == "exponential":
            wait: float = float(2 ** (attempt + 1))
        elif backoff == "linear":
            wait = float(attempt + 1)
        else:  # fixed
            wait = 1.0

        if jitter > 0:
            wait += random.uniform(0, jitter)

        return min(wait, 60.0)

    def _resolve_provider(self, step: Step) -> Any:
        if step.capability not in self.components:
            raise ExecutionError(f"No provider found for capability '{step.capability}'")
        return self.components[step.capability]

    def _build_request(self, step: Step, inputs: dict[str, Any]) -> BaseModel:
        cap_config = self.registry.get_capability(step.capability, "1.0")
        request_model = cap_config.request_model
        if not request_model:
            raise ExecutionError(f"No request_model defined for capability '{step.capability}'")
        return request_model.model_validate(inputs)

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
