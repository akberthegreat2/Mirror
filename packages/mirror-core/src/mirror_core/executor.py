"""Execution engine for DAG pipelines with concurrency, cancellation, retries.

The executor runs an ExecutionPlan with bounded concurrency, state management,
and support for cancellation, timeouts, and retries.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any

from pydantic import BaseModel

from mirror_core.exceptions import ExecutionError
from mirror_core.middleware import MiddlewareChain
from mirror_core.pipeline import Step
from mirror_core.planner import ExecutionPlan
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
    """Executes pipelines with bounded concurrency and state management."""

    def __init__(
        self,
        max_concurrency: int = 10,
        signal_bus: Any | None = None,
        middleware_chain: MiddlewareChain | None = None,
    ):
        self.max_concurrency = max_concurrency
        self.signal_bus = signal_bus
        self.middleware_chain = middleware_chain
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._results: dict[str, ResourceEnvelope] = {}
        self._states: dict[str, StepState] = {}
        self._cancelled = False
        self._producer_ref: ProducerRef | None = None

    def set_producer(self, producer: ProducerRef) -> None:
        """Set the producer reference for wrapping results."""
        self._producer_ref = producer

    async def execute(
        self,
        plan: ExecutionPlan,
        runner: Callable[[Step, dict[str, Any]], Coroutine[Any, Any, Any]],
    ) -> dict[str, ResourceEnvelope]:
        """Execute the plan.

        Args:
            plan: ExecutionPlan from planner.
            runner: Function that executes a step given inputs.

        Returns:
            dict mapping step_id to ResourceEnvelope.
        """
        self._results = {}
        self._states = {step_id: StepState.PENDING for step_id in plan.step_ids}
        self._cancelled = False

        await self._emit("pipeline.started", plan=plan)

        for group in plan.parallel_groups:
            if self._cancelled:
                break

            ready_steps = [
                step_id
                for step_id in group
                if self._states[step_id] == StepState.PENDING and self._can_run(step_id, plan)
            ]

            if not ready_steps:
                continue

            tasks = [self._run_step(step_id, plan, runner) for step_id in ready_steps]
            await asyncio.gather(*tasks, return_exceptions=True)

        await self._emit("pipeline.finished", plan=plan, results=self._results)
        return self._results

    async def _run_step(
        self,
        step_id: str,
        plan: ExecutionPlan,
        runner: Callable[[Step, dict[str, Any]], Coroutine[Any, Any, Any]],
    ) -> None:
        """Run a single step with concurrency control."""
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
                # Wrap execution with middleware if present
                if self.middleware_chain:
                    # Build invocation dict
                    invocation = {
                        "step": step,
                        "inputs": inputs,
                        "context": {
                            "results": self._results,
                            "signal_bus": self.signal_bus,
                        },
                        "metadata": {
                            "execution_id": plan.pipeline_id,
                            "step_id": step_id,
                        },
                    }
                    # Middleware will call the final runner
                    result = await self.middleware_chain.execute(
                        invocation,
                        lambda inv: self._run_capability(inv["step"], inv["inputs"], runner),
                    )
                else:
                    result = await self._run_capability(step, inputs, runner)

                # Wrap result in ResourceEnvelope
                if self._producer_ref is None:
                    raise ExecutionError("ProducerRef not set for executor")
                envelope = ResourceEnvelope.create(
                    resource_type=step.capability.capitalize() + "Result",
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

    async def _run_capability(
        self,
        step: Step,
        inputs: dict[str, Any],
        runner: Callable[[Step, dict[str, Any]], Coroutine[Any, Any, Any]],
    ) -> Any:
        """Run the capability (used as final call in middleware chain)."""
        # If there's a runner in the step config, use it; otherwise call the provided runner
        # The executor's runner is generic, but we can pass the step and inputs.
        return await runner(step, inputs)

    def _resolve_inputs(self, step: Step, plan: ExecutionPlan) -> dict[str, Any]:
        """Resolve step inputs from previous results."""
        inputs = {}
        for target, source in step.input.items():
            if "." in source:
                src_step, output_name = source.split(".", 1)
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
            if self._states.get(dep) not in (StepState.SUCCEEDED, StepState.SKIPPED):
                return False
        return True

    def _evaluate_condition(
        self, condition: str, inputs: dict[str, Any], results: dict[str, Any]
    ) -> bool:
        """Placeholder: safe expression evaluator (future work)."""
        return True

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        if self.signal_bus:
            await self.signal_bus.emit(signal, **kwargs)

    def cancel(self) -> None:
        self._cancelled = True
