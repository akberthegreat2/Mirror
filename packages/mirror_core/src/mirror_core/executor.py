"""Concurrent execution of immutable pipeline plans."""

from __future__ import annotations

import ast
import asyncio
import importlib
import inspect
from collections.abc import Awaitable, Callable, Mapping
from enum import Enum
from typing import Any, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.exceptions import ExecutionError
from mirror_core.middleware import (
    MiddlewareChain,
    MiddlewareContext,
    MiddlewareInvocation,
)
from mirror_core.planner import CompiledStep, ExecutionPlan
from mirror_core.resource import ProducerRef, ResourceEnvelope

Runner = Callable[..., Awaitable[BaseModel]]


class StepState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RunOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    PARTIAL = PARTIALLY_SUCCEEDED
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
        self.tasks: dict[str, asyncio.Task[None]] = {}

    def finish(self) -> ExecutionResult:
        if self.cancelled and self.abort_error is None:
            outcome = RunOutcome.CANCELLED
        elif self.abort_error is not None:
            outcome = RunOutcome.FAILED
        elif any(state is StepState.FAILED for state in self.states.values()):
            outcome = RunOutcome.PARTIALLY_SUCCEEDED
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
    """Reusable DAG engine that creates isolated execution runs."""

    def __init__(
        self,
        components: Mapping[tuple[str, str] | str, Any],
        max_concurrency: int = 10,
        signal_bus: Any | None = None,
        middleware_chain: MiddlewareChain | None = None,
        middleware_chains: Mapping[str, MiddlewareChain] | None = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self.components = components
        self.max_concurrency = max_concurrency
        self.signal_bus = signal_bus
        self.middleware_chain = middleware_chain
        self.middleware_chains = dict(middleware_chains or {})
        self._active_runs: dict[UUID, ExecutionRun] = {}
        self.last_run: ExecutionResult | None = None

    async def execute(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any] | None = None,
        runner: Runner | None = None,
    ) -> dict[str, ResourceEnvelope]:
        result = await self.execute_run(plan, inputs=inputs or {}, runner=runner)
        if result.outcome is RunOutcome.FAILED:
            first_error = next(
                iter(result.errors.values()), "Pipeline execution failed"
            )
            raise ExecutionError(first_error, details={"run_id": str(result.run_id)})
        return result.results

    async def execute_run(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        runner: Runner | None = None,
    ) -> ExecutionResult:
        run = ExecutionRun(plan, inputs)
        self._active_runs[run.run_id] = run
        semaphore = asyncio.Semaphore(self.max_concurrency)
        await self._emit("pipeline.started", run_id=run.run_id, plan=plan)
        try:
            pending = set(plan.step_ids)
            while pending and not run.cancelled and run.abort_error is None:
                ready = [
                    step_id
                    for step_id in plan.order
                    if step_id in pending and self._can_run(run, step_id)
                ]
                if not ready:
                    break
                for step_id in ready:
                    run.states[step_id] = StepState.READY
                    task = asyncio.create_task(
                        self._run_step(run, step_id, semaphore, runner)
                    )
                    run.tasks[step_id] = task
                    pending.remove(step_id)
                done, _ = await asyncio.wait(
                    run.tasks.values(), return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    try:
                        await task
                    except asyncio.CancelledError:
                        if not run.cancelled:
                            raise
                run.tasks = {
                    sid: task for sid, task in run.tasks.items() if not task.done()
                }
            if run.tasks:
                await asyncio.gather(*run.tasks.values(), return_exceptions=True)
            if run.abort_error is not None:
                run.cancelled = True
                self._cancel_pending(run)
            self._skip_unrunnable_steps(run)
            result = run.finish()
            self.last_run = result
            signal = (
                "pipeline.failed"
                if result.outcome is RunOutcome.FAILED
                else "pipeline.finished"
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
            condition_context = self._condition_context(run, compiled, inputs)
            if step.condition and not self._evaluate_condition(
                step.condition, condition_context
            ):
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
                selected_runner = runner_override or self._get_runner(compiled)
                payload = await self._invoke_with_policies(
                    compiled, provider, request, selected_runner, run
                )
                if not isinstance(payload, BaseModel):
                    raise ExecutionError(
                        f"Runner for step {step.id!r} returned {type(payload).__name__}; expected a Pydantic model"
                    )
                expected = compiled.capability.result_model
                if expected is not None and not isinstance(payload, expected):
                    raise ExecutionError(
                        f"Runner for step {step.id!r} returned {type(payload).__name__}; expected {expected.__name__}"
                    )
                producer = ProducerRef(
                    capability=compiled.capability.name,
                    capability_version=compiled.capability.api_version,
                    provider=compiled.provider.name,
                    provider_version=cast(
                        str | None, compiled.provider.metadata.get("version")
                    ),
                    config_fingerprint=run.plan.config_fingerprint,
                    step_id=step.id,
                )
                parents = [
                    run.results[d].resource_id
                    for d in compiled.dependencies
                    if d in run.results
                ]
                envelope = ResourceEnvelope.create(
                    resource_type=expected.__name__
                    if expected is not None
                    else type(payload).__name__,
                    schema_version=compiled.capability.api_version,
                    payload=payload,
                    producer=producer,
                    parents=parents,
                )
                run.results[step.id] = envelope
                run.states[step.id] = StepState.SUCCEEDED
                await self._emit(
                    "step.succeeded", run_id=run.run_id, step=step, result=envelope
                )
            except asyncio.CancelledError:
                run.states[step.id] = StepState.CANCELLED
                raise
            except Exception as exc:
                run.states[step.id] = StepState.FAILED
                run.errors[step.id] = str(exc)
                await self._emit("step.failed", run_id=run.run_id, step=step, error=exc)
                if step.on_error == "abort":
                    run.abort_error = ExecutionError(
                        f"Step {step.id!r} failed: {exc}", cause=exc
                    )
                    self._cancel_tasks(run, except_step=step_id)

    async def _invoke_with_policies(
        self,
        compiled: CompiledStep,
        provider: Any,
        request: BaseModel,
        runner: Runner,
        run: ExecutionRun,
    ) -> BaseModel:
        policy = compiled.definition.retry
        attempts = policy.attempts if policy is not None else 1
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                invocation = self._invoke(compiled, provider, request, runner, run)
                if compiled.definition.timeout is not None:
                    return await asyncio.wait_for(
                        invocation, timeout=compiled.definition.timeout
                    )
                return await invocation
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= attempts:
                    raise
                await self._emit(
                    "step.retrying",
                    run_id=run.run_id,
                    step=compiled.definition,
                    attempt=attempt + 1,
                    error=exc,
                )
                delay = (
                    policy.delay_for_attempt(attempt + 1) if policy is not None else 0.0
                )
                if delay:
                    await asyncio.sleep(delay)
        raise ExecutionError("Retry policy exhausted", cause=last_error)

    async def _invoke(
        self,
        compiled: CompiledStep,
        provider: Any,
        request: BaseModel,
        runner: Runner,
        run: ExecutionRun,
    ) -> BaseModel:
        async def final(invocation: MiddlewareInvocation) -> BaseModel:
            kwargs = self._runner_kwargs(runner, compiled.id, self.signal_bus)
            return await runner(invocation.provider, invocation.request, **kwargs)

        invocation = MiddlewareInvocation(
            step=compiled.definition,
            request=request,
            provider=provider,
            context={
                "run_id": run.run_id,
                "results": run.results,
                "inputs": run.inputs,
                "step_id": compiled.id,
                "signal_bus": self.signal_bus,
            },
            middleware_context=MiddlewareContext(
                run_id=run.run_id,
                pipeline_id=run.plan.pipeline_id,
                step_id=compiled.id,
                capability=compiled.capability.name,
                metadata={"provider": compiled.provider.name},
            ),
        )
        chain = self.middleware_chains.get(
            compiled.capability.name, self.middleware_chain
        )
        return (
            await final(invocation)
            if chain is None
            else cast(BaseModel, await chain.execute(invocation, final))
        )

    def _get_runner(self, compiled: CompiledStep) -> Runner:
        path = compiled.capability.runner
        if path is None:
            raise ExecutionError(
                f"No runner defined for capability {compiled.capability.name!r}"
            )
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
            f"Provider {compiled.provider.name!r} is not initialized for capability {compiled.capability.name!r}"
        )

    @staticmethod
    def _runner_kwargs(
        runner: Runner, step_id: str, signal_bus: Any | None
    ) -> dict[str, Any]:
        try:
            signature = inspect.signature(runner)
        except (TypeError, ValueError):
            return {}

        accepts_var_kwargs = any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )
        kwargs: dict[str, Any] = {}
        if accepts_var_kwargs or "signal_bus" in signature.parameters:
            kwargs["signal_bus"] = signal_bus
        if accepts_var_kwargs or "step_id" in signature.parameters:
            kwargs["step_id"] = step_id
        return kwargs

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
                raise ExecutionError(
                    f"Resource from step {source_step!r} has no output {output!r}"
                )
        return values

    @staticmethod
    def _can_run(run: ExecutionRun, step_id: str) -> bool:
        return all(
            run.states[d] is StepState.SUCCEEDED
            for d in run.plan.get_step(step_id).dependencies
        )

    @staticmethod
    def _cancel_pending(run: ExecutionRun) -> None:
        for step_id, state in run.states.items():
            if state in {StepState.PENDING, StepState.READY}:
                run.states[step_id] = StepState.CANCELLED

    @staticmethod
    def _skip_unrunnable_steps(run: ExecutionRun) -> None:
        for step_id, state in run.states.items():
            if state in {StepState.PENDING, StepState.READY}:
                run.states[step_id] = (
                    StepState.CANCELLED if run.cancelled else StepState.SKIPPED
                )

    @staticmethod
    def _condition_context(
        run: ExecutionRun, compiled: CompiledStep, inputs: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Expose only bound inputs and direct dependency payloads to conditions."""
        context = dict(inputs)
        for dependency in compiled.dependencies:
            envelope = run.results.get(dependency)
            if envelope is not None:
                context[dependency] = envelope.payload
        return context

    @staticmethod
    def _evaluate_condition(condition: str, inputs: Mapping[str, Any]) -> bool:
        normalized = condition.strip().lower()
        if normalized in {"true", "false"}:
            return normalized == "true"
        try:
            tree = ast.parse(condition, mode="eval")
        except SyntaxError as exc:
            raise ExecutionError(
                f"Invalid condition expression: {condition!r}"
            ) from exc

        def evaluate(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return evaluate(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                if node.id not in inputs:
                    raise ExecutionError(f"Unknown condition variable: {node.id!r}")
                return inputs[node.id]
            if isinstance(node, ast.Attribute):
                owner = evaluate(node.value)
                if (
                    isinstance(owner, BaseModel)
                    and node.attr in owner.__class__.model_fields
                ):
                    return getattr(owner, node.attr)
                if isinstance(owner, Mapping) and node.attr in owner:
                    return owner[node.attr]
                raise ExecutionError(f"Unknown condition attribute: {node.attr!r}")
            if isinstance(node, ast.BoolOp):
                vals = [bool(evaluate(v)) for v in node.values]
                if isinstance(node.op, ast.And):
                    return all(vals)
                if isinstance(node.op, ast.Or):
                    return any(vals)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return not bool(evaluate(node.operand))
            if isinstance(node, ast.Compare):
                left = evaluate(node.left)
                for op, comparator in zip(node.ops, node.comparators, strict=True):
                    right = evaluate(comparator)
                    ok = (
                        left == right
                        if isinstance(op, ast.Eq)
                        else left != right
                        if isinstance(op, ast.NotEq)
                        else left < right
                        if isinstance(op, ast.Lt)
                        else left <= right
                        if isinstance(op, ast.LtE)
                        else left > right
                        if isinstance(op, ast.Gt)
                        else left >= right
                        if isinstance(op, ast.GtE)
                        else None
                    )
                    if ok is None:
                        raise ExecutionError(f"Unsupported comparison in {condition!r}")
                    if not ok:
                        return False
                    left = right
                return True
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "exists"
            ):
                if len(node.args) != 1 or node.keywords:
                    raise ExecutionError(
                        f"exists() expects one argument in {condition!r}"
                    )
                arg = node.args[0]
                return (
                    arg.id in inputs
                    if isinstance(arg, ast.Name)
                    else evaluate(arg) is not None
                )
            raise ExecutionError(f"Unsupported condition expression: {condition!r}")

        return bool(evaluate(tree))

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        if self.signal_bus is not None:
            await self.signal_bus.emit(signal, **kwargs)

    @staticmethod
    def _cancel_tasks(run: ExecutionRun, except_step: str | None = None) -> None:
        for step_id, task in run.tasks.items():
            if step_id != except_step and not task.done():
                task.cancel()

    def cancel(self, run_id: UUID | None = None) -> None:
        runs = (
            [self._active_runs[run_id]]
            if run_id is not None and run_id in self._active_runs
            else list(self._active_runs.values())
        )
        for run in runs:
            run.cancelled = True
            self._cancel_tasks(run)
            self._cancel_pending(run)
