"""Tests for the core-owned worker runtime helpers."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from mirror_core.metadata import InMemoryMetadataStore, MetadataNamespaces
from mirror_core.worker_runtime import (
    SQLiteExecutionStore,
    SQLiteLeaseManager,
    WorkerRuntime,
)
from mirror_core.workers import (
    DeadLetterRecord,
    ExecutionRecord,
    InlineWorker,
    InMemoryDeadLetterQueue,
    InMemoryExecutionStore,
    InMemoryLeaseManager,
    JobState,
    SQLiteWorkerBackend,
    WorkerJob,
)


@pytest.mark.asyncio
async def test_worker_runtime_records_execution_and_metadata() -> None:
    """Submitting and finishing a job should persist runtime metadata."""
    backend = InlineWorker()
    await backend.start()
    execution_store = InMemoryExecutionStore()
    dead_letter_queue = InMemoryDeadLetterQueue()
    lease_manager = InMemoryLeaseManager()
    metadata_store = InMemoryMetadataStore()
    runtime = WorkerRuntime(
        backend,
        execution_store=execution_store,
        dead_letter_queue=dead_letter_queue,
        metadata_store=metadata_store,
        lease_manager=lease_manager,
    )

    submitted = await runtime.submit(
        WorkerJob(
            kind="crawl",
            payload={"url": "https://example.com"},
            metadata={"step_id": "step-1"},
        )
    )
    claimed = await runtime.claim("worker-1")
    assert claimed is not None
    assert claimed.job_id == submitted.job_id
    await runtime.heartbeat("worker-1", claimed.job_id)
    completed = await runtime.complete(claimed.job_id)

    assert completed.state is JobState.SUCCEEDED
    assert execution_store.get(submitted.job_id) == ExecutionRecord(
        run_id=submitted.job_id,
        outcome="succeeded",
        payload={"url": "https://example.com"},
        worker_id="worker-1",
        created_at=submitted.submitted_at,
        started_at=claimed.claimed_at,
        completed_at=completed.completed_at,
        metadata={
            "step_id": "step-1",
            "run_id": str(submitted.run_id),
            "pipeline_id": submitted.pipeline_id,
        },
    )
    assert (
        metadata_store.get(MetadataNamespaces.EXECUTION_RUNS, str(submitted.job_id))
        is not None
    )
    assert lease_manager.get(submitted.job_id) is None

    await backend.stop()


@pytest.mark.asyncio
async def test_worker_runtime_routes_failures_to_dlq() -> None:
    """Terminal failures should be persisted and dead-lettered."""
    backend = InlineWorker()
    await backend.start()
    dead_letter_queue = InMemoryDeadLetterQueue()
    runtime = WorkerRuntime(backend, dead_letter_queue=dead_letter_queue)

    submitted = await runtime.submit(
        WorkerJob(kind="crawl", payload={"url": "https://example.com"})
    )
    assert submitted.run_id == submitted.job_id
    assert submitted.pipeline_id == "crawl"
    claimed = await runtime.claim("worker-1")
    assert claimed is not None
    failed = await runtime.fail(claimed.job_id, "boom")

    assert failed.state is JobState.FAILED
    record = dead_letter_queue.get(submitted.job_id)
    expected = DeadLetterRecord(
        run_id=submitted.job_id,
        pipeline_id="crawl",
        step_id=None,
        reason="boom",
        original_inputs={"url": "https://example.com"},
        policy_state={},
        provenance={
            "worker_id": "worker-1",
            "job_id": str(submitted.job_id),
            "run_id": str(submitted.run_id),
        },
        retry_count=0,
        terminal_status="failed",
        worker_id="worker-1",
        lease_id=str(submitted.job_id),
    )
    assert record is not None
    assert record.model_dump(exclude={"created_at"}) == expected.model_dump(
        exclude={"created_at"}
    )

    await backend.stop()


def test_sqlite_runtime_stores_round_trip(tmp_path: Path) -> None:
    """Durable runtime stores should round-trip structured records."""
    execution_store = SQLiteExecutionStore(tmp_path / "execution.sqlite3")
    lease_manager = SQLiteLeaseManager(tmp_path / "leases.sqlite3")
    run_id = UUID("00000000-0000-0000-0000-000000000321")
    record = ExecutionRecord(
        run_id=run_id,
        outcome="succeeded",
        payload={"attempts": 1},
        worker_id="worker-1",
        metadata={"kind": "crawl"},
    )
    execution_store.record(record)
    assert execution_store.get(run_id) == record
    assert execution_store.list() == [record]

    lease = lease_manager.acquire(run_id, "worker-1")
    assert lease_manager.get(run_id) == lease
    renewed = lease_manager.renew(lease)
    assert renewed.job_id == lease.job_id
    lease_manager.release(renewed)
    assert lease_manager.get(run_id) is None


@pytest.mark.asyncio
async def test_worker_runtime_requeues_expired_jobs(tmp_path: Path) -> None:
    """Expired leases should be requeued through the backend contract."""
    backend = SQLiteWorkerBackend(tmp_path / "runtime.sqlite3")
    await backend.start()
    runtime = WorkerRuntime(backend)
    submitted = await runtime.submit(
        WorkerJob(kind="crawl", payload={"url": "https://example.com"})
    )
    assert submitted.run_id == submitted.job_id
    assert submitted.pipeline_id == "crawl"
    claimed = await runtime.claim("worker-1")
    assert claimed is not None
    requeued = await runtime.requeue_expired()
    assert requeued == []
    backend._conn.execute(
        "UPDATE jobs SET lease_expires_at = ? WHERE job_id = ?",
        ("2000-01-01T00:00:00+00:00", str(submitted.job_id)),
    )
    backend._conn.commit()
    requeued = await runtime.requeue_expired()
    assert requeued and requeued[0].state is JobState.QUEUED
    await backend.stop()
