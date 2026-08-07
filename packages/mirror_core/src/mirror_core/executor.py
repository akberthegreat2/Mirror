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
from mirror_core.execution import CapabilityContext, ExecutionContext
from mirror_core.metadata import MetadataRecord, MetadataStore
from mirror_core.middleware import (
    MiddlewareChain,
    MiddlewareContext,
    MiddlewareInvocation,
)
from mirror_core.planner import CompiledStep, ExecutionPlan
from mirror_core.resource import ProducerRef, ResourceEnvelope
from mirror_core.workers import CheckpointStore, DeadLetterQueue, DeadLetterRecord

Runner = Callable[..., Awaitable[BaseModel]]
CompensationHandler = Callable[
    ["ExecutionRun", CompiledStep, Exception], Awaitable[None]
]


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

    def __init__(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        *,
        run_id: UUID | None = None,
    ) -> None:
        missing = sorted(plan.input_names.difference(inputs))
        unknown = sorted(set(inputs).difference(plan.input_names))
        if missing:
            raise ExecutionError(f"Missing pipeline inputs: {', '.join(missing)}")
        if unknown:
            raise ExecutionError(f"Unknown pipeline inputs: {', '.join(unknown)}")
        self.run_id = run_id or uuid4()
        self.plan = plan
        self.inputs = dict(inputs)
        self.results: dict[str, ResourceEnvelope] = {}
        self.states = dict.fromkeys(plan.step_ids, StepState.PENDING)
        self.errors: dict[str, str] = {}
        self.retry_counts: dict[str, int] = {}
        self.failed_step_id: str | None = None
        self.cancelled = False
        self.abort_error: ExecutionError | None = None
        self.tasks: dict[str, asyncio.Task[None]] = {}

    def restore(
        self,
        *,
        states: Mapping[str, StepState],
        results: Mapping[str, ResourceEnvelope],
        errors: Mapping[str, str] | None = None,
        retry_counts: Mapping[str, int] | None = None,
        failed_step_id: str | None = None,
        cancelled: bool = False,
    ) -> None:
        """Restore the run state from a durable checkpoint snapshot."""
        unknown_states = sorted(set(states).difference(self.plan.step_ids))
        unknown_results = sorted(set(results).difference(self.plan.step_ids))
        unknown_errors = sorted(
            set((errors or {}).keys()).difference(self.plan.step_ids)
        )
        unknown_retries = sorted(
            set((retry_counts or {}).keys()).difference(self.plan.step_ids)
        )
        if unknown_states or unknown_results or unknown_errors or unknown_retries:
            details = ", ".join(
                part
                for part in [
                    f"states={unknown_states}" if unknown_states else "",
                    f"results={unknown_results}" if unknown_results else "",
                    f"errors={unknown_errors}" if unknown_errors else "",
                    f"retry_counts={unknown_retries}" if unknown_retries else "",
                ]
                if part
            )
            raise ExecutionError(f"Checkpoint contains unknown step ids: {details}")
        if failed_step_id is not None and failed_step_id not in self.plan.step_ids:
            raise ExecutionError(
                f"Checkpoint references unknown failed step: {failed_step_id!r}"
            )
        self.states.update({name: StepState(value) for name, value in states.items()})
        self.results.update(dict(results))
        self.errors = dict(errors or {})
        self.retry_counts = dict(retry_counts or {})
        self.failed_step_id = failed_step_id
        self.cancelled = cancelled

    def finish(self) -> ExecutionResult:
        if self.cancelled and self.abort_error is None:
            outcome = RunOutcome.CANCELLED
        elif self.abort_error is not None:
            if any(state is StepState.SUCCEEDED for state in self.states.values()):
                outcome = RunOutcome.PARTIALLY_SUCCEEDED
            else:
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
        checkpoint_store: CheckpointStore | None = None,
        dead_letter_queue: DeadLetterQueue | None = None,
        metadata_store: MetadataStore | None = None,
        compensation_handler: CompensationHandler | None = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self.components = components
        self.max_concurrency = max_concurrency
        self.signal_bus = signal_bus
        self.middleware_chain = middleware_chain
        self.middleware_chains = dict(middleware_chains or {})
        self.checkpoint_store = checkpoint_store
        self.dead_letter_queue = dead_letter_queue
        self.metadata_store = metadata_store
        self.compensation_handler = compensation_handler
        self._active_runs: dict[UUID, ExecutionRun] = {}
        self.last_run: ExecutionResult | None = None

    async def execute(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any] | None = None,
        runner: Runner | None = None,
        resume_from: tuple[UUID, str] | None = None,
    ) -> dict[str, ResourceEnvelope]:
        result = await self.execute_run(
            plan, inputs=inputs or {}, runner=runner, resume_from=resume_from
        )
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
        resume_from: tuple[UUID, str] | None = None,
    ) -> ExecutionResult:
        run = ExecutionRun(plan, inputs, run_id=resume_from[0] if resume_from else None)
        if resume_from is not None:
            self._restore_from_checkpoint(run, resume_from)
        self._active_runs[run.run_id] = run
        self._record_metadata(
            MetadataRecord.execution_run(
                run.run_id,
                payload={
                    "pipeline_id": plan.pipeline_id,
                    "config_fingerprint": plan.config_fingerprint,
                    "input_names": sorted(plan.input_names),
                    "step_ids": list(plan.step_ids),
                },
            )
        )
        self._record_metadata(
            MetadataRecord.policy_snapshot(
                run.run_id,
                payload={
                    step_id: compiled.policy.model_dump(mode="json")
                    for step_id, compiled in plan.steps.items()
                },
            )
        )
        semaphore = asyncio.Semaphore(self.max_concurrency)
        await self._emit("pipeline.started", run_id=run.run_id, plan=plan)
        try:
            pending = {
                step_id
                for step_id in plan.step_ids
                if run.states.get(step_id)
                not in {StepState.SUCCEEDED, StepState.SKIPPED, StepState.CANCELLED}
            }
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
            self._record_metadata(
                MetadataRecord.terminal_outcome(
                    run.run_id,
                    payload={
                        "pipeline_id": run.plan.pipeline_id,
                        "outcome": result.outcome.value,
                        "errors": dict(result.errors),
                        "states": {
                            step_id: state.value
                            for step_id, state in result.states.items()
                        },
                    },
                )
            )
            await self._emit(
                "pipeline.failed"
                if result.outcome is RunOutcome.FAILED
                else "pipeline.finished",
                run_id=run.run_id,
                result=result,
            )
            if result.outcome in {RunOutcome.FAILED, RunOutcome.PARTIALLY_SUCCEEDED}:
                await self._record_dead_letter(run, result)
            return result
        finally:
            self._active_runs.pop(run.run_id, None)

    async def resume_from_checkpoint(
        self,
        plan: ExecutionPlan,
        *,
        run_id: UUID,
        step_id: str | None = None,
        inputs: Mapping[str, Any] | None = None,
        runner: Runner | None = None,
    ) -> ExecutionResult:
        """Resume a run from the latest or a specific checkpoint snapshot."""
        if self.checkpoint_store is None:
            raise ExecutionError("No checkpoint store is configured for resume")
        if step_id is None:
            latest = self.checkpoint_store.latest(run_id)
            if latest is None:
                raise ExecutionError(f"No checkpoint available for run {run_id}")
            step_id, snapshot = latest
        else:
            snapshot = self.checkpoint_store.load(run_id, step_id)
            if snapshot is None:
                raise ExecutionError(
                    f"No checkpoint available for run {run_id} step {step_id!r}"
                )
        self._record_metadata(
            MetadataRecord.replay_pointer(
                run_id,
                step_id,
                payload={"mode": "resume", "pipeline_id": plan.pipeline_id},
            )
        )
        resume_inputs = inputs or snapshot.get("inputs", {})
        return await self.execute_run(
            plan,
            inputs=resume_inputs,
            runner=runner,
            resume_from=(run_id, step_id),
        )

    async def replay_dead_letter(
        self,
        plan: ExecutionPlan,
        *,
        run_id: UUID,
        inputs: Mapping[str, Any] | None = None,
        runner: Runner | None = None,
    ) -> ExecutionResult:
        """Replay a dead-lettered execution from the latest durable checkpoint."""
        if self.dead_letter_queue is None:
            raise ExecutionError("No dead letter queue is configured for replay")
        record = self.dead_letter_queue.replay(run_id)
        if record is None:
            raise ExecutionError(f"No dead-letter record available for run {run_id}")
        self._record_metadata(
            MetadataRecord.replay_pointer(
                run_id,
                record.step_id or "dead-letter",
                payload={"mode": "dead_letter", "pipeline_id": plan.pipeline_id},
            )
        )
        return await self.resume_from_checkpoint(
            plan,
            run_id=run_id,
            inputs=inputs or record.original_inputs,
            runner=runner,
        )

    def _restore_from_checkpoint(
        self,
        run: ExecutionRun,
        resume_from: tuple[UUID, str],
    ) -> None:
        if self.checkpoint_store is None:
            raise ExecutionError("No checkpoint store is configured for resume")
        run_id, step_id = resume_from
        snapshot = self.checkpoint_store.load(run_id, step_id)
        if snapshot is None:
            raise ExecutionError(
                f"No checkpoint available for run {run_id} step {step_id!r}"
            )
        snapshot_run_id = snapshot.get("run_id")
        if snapshot_run_id is not None and str(snapshot_run_id) != str(run_id):
            raise ExecutionError(
                f"Checkpoint run_id mismatch for run {run_id} step {step_id!r}"
            )
        if snapshot.get("pipeline_id") not in {None, run.plan.pipeline_id}:
            raise ExecutionError(
                f"Checkpoint pipeline mismatch for run {run_id} step {step_id!r}"
            )
        states = {
            name: StepState(value) for name, value in snapshot.get("states", {}).items()
        }
        results = {
            name: self._restore_envelope(value)
            for name, value in snapshot.get("results", {}).items()
        }
        run.restore(
            states=states,
            results=results,
            errors=snapshot.get("errors", {}),
            retry_counts=snapshot.get("retry_counts", {}),
            failed_step_id=snapshot.get("failed_step_id"),
            cancelled=bool(snapshot.get("cancelled", False)),
        )
        if snapshot.get("inputs"):
            run.inputs = dict(snapshot["inputs"])

    @staticmethod
    def _restore_envelope(value: Mapping[str, Any]) -> ResourceEnvelope:
        envelope_data = dict(value.get("envelope", value))
        payload_data = value.get("payload")
        payload_type = value.get("payload_type")
        payload: BaseModel | Any = payload_data
        if payload_type:
            payload = Executor._restore_model(payload_type, payload_data)
        envelope_data["payload"] = payload
        return ResourceEnvelope.model_validate(envelope_data)

    @staticmethod
    def _restore_model(type_path: str, payload: Any) -> Any:
        if payload is None:
            return None
        module_path, _, class_name = type_path.rpartition(":")
        try:
            module = importlib.import_module(module_path)
            model_type = getattr(module, class_name)
            if isinstance(model_type, type) and issubclass(model_type, BaseModel):
                return model_type.model_validate(payload)
        except Exception:
            pass
        return payload

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
            self._record_metadata(
                MetadataRecord.step_run(
                    run.run_id,
                    step.id,
                    payload={
                        "state": StepState.RUNNING.value,
                        "capability": compiled.capability.name,
                        "provider": compiled.provider.name,
                        "dependencies": sorted(compiled.dependencies),
                    },
                )
            )
            await self._emit("step.started", run_id=run.run_id, step=step)
            try:
                request_model = compiled.capability.request_model
                if request_model is None:
                    raise ExecutionError(
                        f"Capability {compiled.capability.name!r} has no request model"
                    )
                request = request_model.model_validate(inputs)
                selected_runner = runner_override or self._get_runner(compiled)
                payload, provider_config = await self._invoke_with_fallbacks(
                    compiled, request, selected_runner, run
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
                    provider=provider_config.name,
                    provider_version=cast(
                        str | None, provider_config.metadata.get("version")
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
                self._record_metadata(
                    MetadataRecord.step_run(
                        run.run_id,
                        step.id,
                        payload={
                            "state": StepState.SUCCEEDED.value,
                            "resource_id": str(envelope.resource_id),
                            "parents": [str(parent) for parent in parents],
                            "producer": producer.model_dump(mode="json"),
                        },
                    )
                )
                self._record_metadata(
                    MetadataRecord.lineage(
                        envelope.resource_id,
                        payload={
                            "run_id": str(run.run_id),
                            "step_id": step.id,
                            "parents": [str(parent) for parent in parents],
                        },
                    )
                )
                self._record_metadata(
                    MetadataRecord.provenance(
                        envelope.resource_id,
                        payload={
                            "run_id": str(run.run_id),
                            "step_id": step.id,
                            "producer": producer.model_dump(mode="json"),
                        },
                    )
                )
                self._save_checkpoint(run, compiled, step)
                await self._emit(
                    "step.succeeded", run_id=run.run_id, step=step, result=envelope
                )
            except asyncio.CancelledError:
                run.states[step.id] = StepState.CANCELLED
                raise
            except Exception as exc:  # noqa: BLE001
                run.states[step.id] = StepState.FAILED
                run.failed_step_id = step.id
                run.errors[step.id] = str(exc)
                self._record_metadata(
                    MetadataRecord.step_run(
                        run.run_id,
                        step.id,
                        payload={
                            "state": StepState.FAILED.value,
                            "error": str(exc),
                            "policy": compiled.policy.model_dump(mode="json"),
                        },
                    )
                )
                await self._emit("step.failed", run_id=run.run_id, step=step, error=exc)
                if compiled.policy.compensation is not None:
                    await self._invoke_compensation(run, compiled, exc)
                if compiled.policy.on_error == "abort":
                    run.abort_error = ExecutionError(
                        f"Step {step.id!r} failed: {exc}", cause=exc
                    )
                    self._cancel_tasks(run, except_step=step_id)

    async def _invoke_with_fallbacks(
        self,
        compiled: CompiledStep,
        request: BaseModel,
        runner: Runner,
        run: ExecutionRun,
    ) -> tuple[BaseModel, Any]:
        provider_configs = (compiled.provider, *compiled.fallback_providers)
        last_error: Exception | None = None
        for index, provider_config in enumerate(provider_configs):
            provider = self._get_provider(compiled, provider_config)
            try:
                payload = await self._invoke_with_policies(
                    compiled, provider, provider_config, request, runner, run
                )
                if index > 0:
                    await self._emit(
                        "step.fallback.succeeded",
                        run_id=run.run_id,
                        step=compiled.definition,
                        provider=provider_config.name,
                        result=payload,
                    )
                return payload, provider_config
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_error = exc
                if index < len(provider_configs) - 1:
                    await self._emit(
                        "step.fallback.attempted",
                        run_id=run.run_id,
                        step=compiled.definition,
                        provider=provider_config.name,
                        error=exc,
                    )
                    continue
                raise
        raise ExecutionError("Fallback providers exhausted", cause=last_error)

    async def _invoke_with_policies(
        self,
        compiled: CompiledStep,
        provider: Any,
        provider_config: Any,
        request: BaseModel,
        runner: Runner,
        run: ExecutionRun,
    ) -> BaseModel:
        policy = compiled.policy
        attempts = policy.retry.attempts if policy.retry is not None else 1
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                invocation = self._invoke(
                    compiled, provider, provider_config, request, runner, run
                )
                if policy.timeout is not None:
                    return await asyncio.wait_for(invocation, timeout=policy.timeout)
                return await invocation
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_error = exc
                run.retry_counts[compiled.id] = attempt
                if attempt >= attempts:
                    raise
                self._record_metadata(
                    MetadataRecord.retry(
                        run.run_id,
                        compiled.id,
                        attempt + 1,
                        payload={
                            "error": str(exc),
                            "policy": policy.model_dump(mode="json"),
                        },
                    )
                )
                await self._emit(
                    "step.retrying",
                    run_id=run.run_id,
                    step=compiled.definition,
                    attempt=attempt + 1,
                    error=exc,
                    policy=policy.model_dump(mode="json"),
                )
                delay = (
                    policy.retry.delay_for_attempt(attempt + 1)
                    if policy.retry is not None
                    else 0.0
                )
                if delay:
                    await asyncio.sleep(delay)
        raise ExecutionError("Retry policy exhausted", cause=last_error)

    async def _invoke(
        self,
        compiled: CompiledStep,
        provider: Any,
        provider_config: Any,
        request: BaseModel,
        runner: Runner,
        run: ExecutionRun,
    ) -> BaseModel:
        execution_context = ExecutionContext(
            run_id=run.run_id,
            pipeline_id=run.plan.pipeline_id,
            inputs=run.inputs,
            results=run.results,
            metadata={"step_id": compiled.id},
        )
        capability_context = CapabilityContext.from_execution(
            execution_context,
            step_id=compiled.id,
            capability=compiled.capability.name,
            capability_version=compiled.capability.api_version,
            provider=provider_config.name,
            provider_version=cast(str | None, provider_config.metadata.get("version")),
            policy=compiled.policy,
            metadata={"provider": provider_config.name},
        )

        async def final(invocation: MiddlewareInvocation) -> BaseModel:
            kwargs = self._runner_kwargs(
                runner,
                compiled.id,
                self.signal_bus,
                execution_context,
                capability_context,
                invocation.middleware_context,
            )
            return await runner(invocation.provider, invocation.request, **kwargs)

        invocation = MiddlewareInvocation(
            step=compiled.definition,
            request=request,
            provider=provider,
            execution_context=execution_context,
            capability_context=capability_context,
            context={
                "run_id": run.run_id,
                "pipeline_id": run.plan.pipeline_id,
                "results": run.results,
                "inputs": run.inputs,
                "step_id": compiled.id,
                "signal_bus": self.signal_bus,
            },
            middleware_context=MiddlewareContext(
                execution=execution_context,
                step_id=compiled.id,
                capability=compiled.capability.name,
                capability_version=compiled.capability.api_version,
                provider=provider_config.name,
                provider_version=cast(
                    str | None, provider_config.metadata.get("version")
                ),
                policy=compiled.policy,
                metadata={"provider": provider_config.name},
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

    def _get_provider(self, compiled: CompiledStep, provider_config: Any) -> Any:
        exact_key = (compiled.capability.name, provider_config.name)
        if exact_key in self.components:
            return self.components[exact_key]
        if compiled.capability.name in self.components:
            return self.components[compiled.capability.name]
        raise ExecutionError(
            f"Provider {provider_config.name!r} is not initialized for capability {compiled.capability.name!r}"
        )

    def _save_checkpoint(
        self, run: ExecutionRun, compiled: CompiledStep, step: Any
    ) -> None:
        if self.checkpoint_store is None:
            return
        payload = {
            "run_id": str(run.run_id),
            "pipeline_id": run.plan.pipeline_id,
            "step_id": step.id,
            "states": {step_id: state.value for step_id, state in run.states.items()},
            "errors": dict(run.errors),
            "retry_counts": dict(run.retry_counts),
            "failed_step_id": run.failed_step_id,
            "cancelled": run.cancelled,
            "inputs": dict(run.inputs),
            "results": {
                step_id: self._serialize_envelope(envelope)
                for step_id, envelope in run.results.items()
            },
            "metadata": {"config_fingerprint": run.plan.config_fingerprint},
        }
        self.checkpoint_store.save(run.run_id, step.id, payload)

    def _record_metadata(self, record: MetadataRecord) -> None:
        if self.metadata_store is None:
            return
        self.metadata_store.put(record)

    async def _invoke_compensation(
        self,
        run: ExecutionRun,
        compiled: CompiledStep,
        error: Exception,
    ) -> None:
        """Invoke the configured compensation hook best-effort.

        Compensation is observational and does not override the original failure.
        """
        self._record_metadata(
            MetadataRecord.audit_event(
                run.run_id,
                "compensation.triggered",
                payload={
                    "step_id": compiled.id,
                    "capability": compiled.capability.name,
                    "provider": compiled.provider.name,
                    "policy": compiled.policy.compensation.model_dump(mode="json")
                    if compiled.policy.compensation is not None
                    else {},
                    "error": str(error),
                },
            )
        )
        if self.compensation_handler is None:
            return
        try:
            await self.compensation_handler(run, compiled, error)
        except Exception as comp_exc:  # noqa: BLE001
            run.errors[f"{compiled.id}:compensation"] = str(comp_exc)
            self._record_metadata(
                MetadataRecord.audit_event(
                    run.run_id,
                    "compensation.failed",
                    payload={
                        "step_id": compiled.id,
                        "capability": compiled.capability.name,
                        "provider": compiled.provider.name,
                        "error": str(comp_exc),
                    },
                )
            )

    async def _record_dead_letter(
        self, run: ExecutionRun, result: ExecutionResult
    ) -> None:
        if self.dead_letter_queue is None:
            return
        record = DeadLetterRecord(
            run_id=run.run_id,
            pipeline_id=run.plan.pipeline_id,
            step_id=run.failed_step_id,
            reason=next(iter(result.errors.values()), "execution failed"),
            original_inputs=dict(run.inputs),
            policy_state={
                step_id: compiled.policy.model_dump(mode="json")
                for step_id, compiled in run.plan.steps.items()
            },
            provenance={
                step_id: envelope.resource_id
                for step_id, envelope in run.results.items()
            },
            retry_count=sum(run.retry_counts.values()),
            terminal_status=result.outcome.value,
        )
        self.dead_letter_queue.record(record)

    @staticmethod
    def _serialize_envelope(envelope: ResourceEnvelope) -> dict[str, Any]:
        return {
            "envelope": envelope.model_dump(mode="json"),
            "payload_type": (
                f"{envelope.payload.__class__.__module__}:{envelope.payload.__class__.__qualname__}"
            ),
            "payload": envelope.payload.model_dump(mode="json"),
        }

    @staticmethod
    def _runner_kwargs(
        runner: Runner,
        step_id: str,
        signal_bus: Any | None,
        execution_context: ExecutionContext | None = None,
        capability_context: CapabilityContext | None = None,
        middleware_context: MiddlewareContext | None = None,
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
        if execution_context is not None and (
            accepts_var_kwargs or "execution_context" in signature.parameters
        ):
            kwargs["execution_context"] = execution_context
        if capability_context is not None and (
            accepts_var_kwargs or "capability_context" in signature.parameters
        ):
            kwargs["capability_context"] = capability_context
        if middleware_context is not None and (
            accepts_var_kwargs or "middleware_context" in signature.parameters
        ):
            kwargs["middleware_context"] = middleware_context
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
            elif isinstance(payload, Mapping) and output in payload:
                values[target] = payload[output]
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
