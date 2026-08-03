"""Concurrent execution of immutable pipeline plans."""

from __future__ import annotations

import ast
import asyncio
import importlib
from collections.abc import Awaitable, Callable, Mapping
from enum import Enum
from typing import Any, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.exceptions import ExecutionError
from mirror_core.middleware import MiddlewareChain
from mirror_core.planner import CompiledStep, ExecutionPlan
from mirror_core.resource import ProducerRef, ResourceEnvelope

Runner = Callable[..., Awaitable[BaseModel]]


class StepState(str, Enum):
    """Runtime state of one pipeline step."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RunOutcome(str, Enum):
    """Terminal outcome of a pipeline invocation."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class ExecutionResult(BaseModel):
    """Immutable public summary of a completed execution run."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    run_id: UUID
    pipeline_id: str
    outcome: RunOutcome
    results: dict[str, ResourceEnvelope]
    states: dict[str, StepState]
    errors: dict[str, str] = Field(default_factory=dict)


class ExecutionRun:
    """Mutable state belonging to exactly one execution invocation."""

    def __init__(self, plan: ExecutionPlan, inputs: Mapping[str, Any]) -> None:
        missing = sorted(plan.input_names.difference(inputs))
        unknown = sorted(set(inputs).difference(plan.input_names))
        if missing:
            raise ExecutionError(f"Missing pipeline inputs: {', '.join(missing)}")
        if unknown:
            raise ExecutionError(f"Unknown pipeline inputs: {', '.join(unknown)}")
        self.run_id = uuid4()
        self.plan = plan
        self.inputs = dict(inputs)
        self.results: dict[str, ResourceEnvelope] = {}
        self.states = dict.fromkeys(plan.step_ids, StepState.PENDING)
        self.errors: dict[str, str] = {}
        self.cancelled = False
        self.abort_error: ExecutionError | None = None

    def finish(self) -> ExecutionResult:
        if self.cancelled and self.abort_error is None:
            outcome = RunOutcome.CANCELLED
        elif self.abort_error is not None:
            outcome = RunOutcome.FAILED
        elif any(state is StepState.FAILED for state in self.states.values()):
            outcome = RunOutcome.PARTIAL
        else:
            outcome = RunOutcome.SUCCEEDED
        return ExecutionResult(
            run_id=self.run_id,
            pipeline_id=self.plan.pipeline_id,
            outcome=outcome,
            results=dict(self.results),
            states=dict(self.states),
            errors=dict(self.errors),
        )


class Executor:
    """Reusable engine that creates isolated :class:`ExecutionRun` objects."""

    def __init__(
        self,
        components: Mapping[tuple[str, str] | str, Any],
        max_concurrency: int = 10,
        signal_bus: Any | None = None,
        middleware_chain: MiddlewareChain | None = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self.components = components
        self.max_concurrency = max_concurrency
        self.signal_bus = signal_bus
        self.middleware_chain = middleware_chain
        self._active_runs: dict[UUID, ExecutionRun] = {}
        self.last_run: ExecutionResult | None = None

    async def execute(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any] | None = None,
        runner: Runner | None = None,
    ) -> dict[str, ResourceEnvelope]:
        """Execute a plan and return step resources.

        Raises:
            ExecutionError: If an aborting step fails.
        """
        result = await self.execute_run(plan, inputs=inputs or {}, runner=runner)
        if result.outcome is RunOutcome.FAILED:
            first_error = next(iter(result.errors.values()), "Pipeline execution failed")
            raise ExecutionError(first_error, details={"run_id": str(result.run_id)})
        return result.results

    async def execute_run(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        runner: Runner | None = None,
    ) -> ExecutionResult:
        """Execute a plan and return its complete terminal state."""
        run = ExecutionRun(plan, inputs)
        self._active_runs[run.run_id] = run
        semaphore = asyncio.Semaphore(self.max_concurrency)
        await self._emit("pipeline.started", run_id=run.run_id, plan=plan)
        try:
            for group in plan.parallel_groups:
                if run.cancelled:
                    break
                tasks = [
                    asyncio.create_task(self._run_step(run, step_id, semaphore, runner))
                    for step_id in group
                    if self._can_run(run, step_id)
                ]
                if tasks:
                    await asyncio.gather(*tasks)
                if run.abort_error is not None:
                    run.cancelled = True
                    self._cancel_pending(run)
                    break
            self._skip_unrunnable_steps(run)
            result = run.finish()
            self.last_run = result
            signal = (
                "pipeline.failed" if result.outcome is RunOutcome.FAILED else "pipeline.finished"
            )
            await self._emit(signal, run_id=run.run_id, result=result)
            return result
        finally:
            self._active_runs.pop(run.run_id, None)

    async def _run_step(
        self,
        run: ExecutionRun,
        step_id: str,
        semaphore: asyncio.Semaphore,
        runner_override: Runner | None,
    ) -> None:
        async with semaphore:
            if run.cancelled:
                run.states[step_id] = StepState.CANCELLED
                return
            compiled = run.plan.get_step(step_id)
            step = compiled.definition
            inputs = self._resolve_inputs(run, compiled)
            if step.condition and not self._evaluate_condition(step.condition, inputs):
                run.states[step_id] = StepState.SKIPPED
                await self._emit("step.skipped", run_id=run.run_id, step=step)
                return

            run.states[step_id] = StepState.RUNNING
            await self._emit("step.started", run_id=run.run_id, step=step)
            try:
                provider = self._get_provider(compiled)
                request_model = compiled.capability.request_model
                if request_model is None:
                    raise ExecutionError(
                        f"Capability {compiled.capability.name!r} has no request model"
                    )
                request = request_model.model_validate(inputs)
                runner = runner_override or self._get_runner(compiled)
                payload = await self._invoke(compiled, provider, request, runner, run)
                if not isinstance(payload, BaseModel):
                    raise ExecutionError(
                        f"Runner for step {step.id!r} returned {type(payload).__name__}; "
                        "expected a Pydantic model"
                    )
                expected = compiled.capability.result_model
                if expected is not None and not isinstance(payload, expected):
                    raise ExecutionError(
                        f"Runner for step {step.id!r} returned {type(payload).__name__}; "
                        f"expected {expected.__name__}"
                    )
                producer = ProducerRef(
                    capability=compiled.capability.name,
                    capability_version=compiled.capability.api_version,
                    provider=compiled.provider.name,
                    provider_version=cast(str | None, compiled.provider.metadata.get("version")),
                    config_fingerprint=run.plan.config_fingerprint,
                    step_id=step.id,
                )
                parents = [
                    run.results[dependency].resource_id
                    for dependency in compiled.dependencies
                    if dependency in run.results
                ]
                envelope = ResourceEnvelope.create(
                    resource_type=(
                        compiled.capability.result_model.__name__
                        if compiled.capability.result_model is not None
                        else type(payload).__name__
                    ),
                    schema_version=compiled.capability.api_version,
                    payload=payload,
                    producer=producer,
                    parents=parents,
                )
                run.results[step.id] = envelope
                run.states[step.id] = StepState.SUCCEEDED
                await self._emit("step.succeeded", run_id=run.run_id, step=step, result=envelope)
            except Exception as exc:
                run.states[step.id] = StepState.FAILED
                run.errors[step.id] = str(exc)
                await self._emit("step.failed", run_id=run.run_id, step=step, error=exc)
                if step.on_error == "abort":
                    run.abort_error = ExecutionError(f"Step {step.id!r} failed: {exc}", cause=exc)
                elif step.on_error == "fallback":
                    run.abort_error = ExecutionError(
                        f"Step {step.id!r} requests fallback, but no compiled fallback exists"
                    )

    async def _invoke(
        self,
        compiled: CompiledStep,
        provider: Any,
        request: BaseModel,
        runner: Runner,
        run: ExecutionRun,
    ) -> BaseModel:
        async def final(invocation: dict[str, Any]) -> BaseModel:
            return await runner(
                invocation["provider"],
                invocation["request"],
                signal_bus=self.signal_bus,
                step_id=compiled.id,
            )

        invocation = {
            "step": compiled.definition,
            "request": request,
            "provider": provider,
            "context": {"run_id": run.run_id, "results": run.results},
        }
        if self.middleware_chain is None:
            return await final(invocation)
        return cast(BaseModel, await self.middleware_chain.execute(invocation, final))

    def _get_runner(self, compiled: CompiledStep) -> Runner:
        path = compiled.capability.runner
        if path is None:
            raise ExecutionError(f"No runner defined for capability {compiled.capability.name!r}")
        module_path, separator, name = path.rpartition(":")
        if not separator:
            raise ExecutionError(f"Invalid runner import path: {path!r}")
        return cast(Runner, getattr(importlib.import_module(module_path), name))

    def _get_provider(self, compiled: CompiledStep) -> Any:
        exact_key = (compiled.capability.name, compiled.provider.name)
        if exact_key in self.components:
            return self.components[exact_key]
        if compiled.capability.name in self.components:
            return self.components[compiled.capability.name]
        raise ExecutionError(
            f"Provider {compiled.provider.name!r} is not initialized for "
            f"capability {compiled.capability.name!r}"
        )

    @staticmethod
    def _resolve_inputs(run: ExecutionRun, compiled: CompiledStep) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for target, source in compiled.definition.input.items():
            source_step, output = source.split(".", 1)
            if source_step == "$pipeline":
                values[target] = run.inputs[output]
                continue
            envelope = run.results.get(source_step)
            if envelope is None:
                raise ExecutionError(
                    f"Missing dependency resource {source_step!r} for step {compiled.id!r}"
                )
            payload = envelope.payload
            if output == "result":
                values[target] = payload
            elif hasattr(payload, output):
                values[target] = getattr(payload, output)
            else:
                raise ExecutionError(f"Resource from step {source_step!r} has no output {output!r}")
        return values

    @staticmethod
    def _can_run(run: ExecutionRun, step_id: str) -> bool:
        compiled = run.plan.get_step(step_id)
        return all(
            run.states[dependency] is StepState.SUCCEEDED for dependency in compiled.dependencies
        )

    @staticmethod
    def _cancel_pending(run: ExecutionRun) -> None:
        for step_id, state in run.states.items():
            if state is StepState.PENDING:
                run.states[step_id] = StepState.CANCELLED

    @staticmethod
    def _skip_unrunnable_steps(run: ExecutionRun) -> None:
        for step_id, state in run.states.items():
            if state is StepState.PENDING:
                run.states[step_id] = StepState.SKIPPED

    @staticmethod
    def _evaluate_condition(condition: str, inputs: Mapping[str, Any]) -> bool:
        """Evaluate a deliberately small, side-effect-free expression subset."""
        normalized = condition.strip().lower()
        if normalized in {"true", "false"}:
            return normalized == "true"
        try:
            tree = ast.parse(condition, mode="eval")
        except SyntaxError as exc:
            raise ExecutionError(f"Invalid condition expression: {condition!r}") from exc
        allowed = (
            ast.Expression,
            ast.BoolOp,
            ast.And,
            ast.Or,
            ast.UnaryOp,
            ast.Not,
            ast.Compare,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Name,
            ast.Constant,
            ast.Load,
        )
        if any(not isinstance(node, allowed) for node in ast.walk(tree)):
            raise ExecutionError(f"Unsupported condition expression: {condition!r}")
        return bool(
            eval(compile(tree, "<mirror-condition>", "eval"), {"__builtins__": {}}, dict(inputs))
        )

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        if self.signal_bus is not None:
            await self.signal_bus.emit(signal, **kwargs)

    def cancel(self, run_id: UUID | None = None) -> None:
        """Cancel one run, or all active runs when no ID is supplied."""
        runs = (
            [self._active_runs[run_id]]
            if run_id is not None and run_id in self._active_runs
            else list(self._active_runs.values())
        )
        for run in runs:
            run.cancelled = True
