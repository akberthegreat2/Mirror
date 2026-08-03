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

from mirror_core.exceptions import ExecutionError
from mirror_core.pipeline import Step
from mirror_core.planner import ExecutionPlan

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
    ):
        self.max_concurrency = max_concurrency
        self.signal_bus = signal_bus
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._results: dict[str, Any] = {}
        self._states: dict[str, StepState] = {}
        self._cancelled = False

    async def execute(
        self,
        plan: ExecutionPlan,
        runner: Callable[[Step, dict[str, Any]], Coroutine[Any, Any, Any]],
    ) -> dict[str, Any]:
        """Execute the plan.

        Args:
            plan: ExecutionPlan from planner.
            runner: Function that executes a step given inputs.

        Returns:
            dict mapping step_id to result.
        """
        self._results = {}
        self._states = {step_id: StepState.PENDING for step_id in plan.step_ids}
        self._cancelled = False

        await self._emit("pipeline.started", plan=plan)

        # Process nodes in parallel groups
        for group in plan.parallel_groups:
            if self._cancelled:
                break

            # Check if group can run (all dependencies satisfied)
            ready_steps = [
                step_id
                for step_id in group
                if self._states[step_id] == StepState.PENDING and self._can_run(step_id, plan)
            ]

            if not ready_steps:
                continue

            # Run group in parallel
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

            # Build inputs from dependencies
            inputs = self._resolve_inputs(step, plan)

            # Check condition
            if step.condition and not self._evaluate_condition(
                step.condition, inputs, self._results
            ):
                self._states[step_id] = StepState.SKIPPED
                await self._emit("step.skipped", step=step)
                return

            try:
                result = await self._run_with_retry(step, inputs, runner)
                self._results[step_id] = result
                self._states[step_id] = StepState.SUCCEEDED
                await self._emit("step.succeeded", step=step, result=result)

            except Exception as e:
                self._states[step_id] = StepState.FAILED
                await self._emit("step.failed", step=step, error=str(e))
                if step.on_error == "abort":
                    self._cancelled = True
                    raise ExecutionError(f"Step {step.id} failed", cause=e) from e

    def _resolve_inputs(self, step: Step, plan: ExecutionPlan) -> dict[str, Any]:
        """Resolve step inputs from previous results."""
        inputs = {}
        for target, source in step.input.items():
            if "." in source:
                src_step, output_name = source.split(".", 1)
                result = self._results.get(src_step)
                if result is None:
                    raise ExecutionError(f"Missing dependency: {src_step} -> {step.id}")
                inputs[target] = getattr(result, output_name, None)
            else:
                # pipeline input
                inputs[target] = source
        return inputs

    def _can_run(self, step_id: str, plan: ExecutionPlan) -> bool:
        """Check if all dependencies are satisfied."""
        deps = plan.dependencies.get(step_id, set())
        for dep in deps:
            if self._states.get(dep) not in (
                StepState.SUCCEEDED,
                StepState.SKIPPED,
            ):
                return False
        return True

    def _evaluate_condition(
        self, condition: str, inputs: dict[str, Any], results: dict[str, Any]
    ) -> bool:
        """Evaluate a condition using a safe expression language.

        This is a placeholder. In production, use a safe expression evaluator
        (e.g., a restricted Python AST or a custom language).
        """
        # Simple placeholder: avoid eval/exec
        # In real implementation, use a restricted parser
        return True

    async def _run_with_retry(
        self,
        step: Step,
        inputs: dict[str, Any],
        runner: Callable[[Step, dict[str, Any]], Coroutine[Any, Any, Any]],
    ) -> Any:
        """Run a step with retry policy."""
        attempts = step.retry.get("attempts", 1) if step.retry else 1
        backoff = step.retry.get("backoff", "fixed") if step.retry else "fixed"
        jitter = step.retry.get("jitter", 0.0) if step.retry else 0.0

        last_exception = None

        for attempt in range(attempts):
            try:
                if attempt > 0:
                    await self._emit("step.retrying", step=step, attempt=attempt)
                return await runner(step, inputs)
            except Exception as e:
                last_exception = e
                if attempt < attempts - 1:
                    wait = self._calculate_backoff(attempt, backoff, jitter)
                    await asyncio.sleep(wait)

        raise ExecutionError(
            f"Step {step.id} failed after {attempts} attempts",
            cause=last_exception,
        )

    def _calculate_backoff(self, attempt: int, backoff: str, jitter: float) -> float:
        """Calculate backoff delay."""
        if backoff == "exponential":
            wait = 2 ** (attempt + 1)
        elif backoff == "linear":
            wait = attempt + 1
        else:  # fixed
            wait = 1.0

        if jitter > 0:
            import random

            wait += random.uniform(0, jitter)

        return min(wait, 60.0)  # type: ignore[no-any-return]

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        """Emit a signal if bus is available."""
        if self.signal_bus:
            await self.signal_bus.emit(signal, **kwargs)

    def cancel(self) -> None:
        """Cancel execution."""
        self._cancelled = True
