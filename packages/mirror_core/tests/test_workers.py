"""Tests for worker contracts and in-memory implementations."""

from __future__ import annotations

from uuid import UUID

import pytest
from mirror_core.workers import (
    DeadLetterRecord,
    ExecutionRecord,
    InlineWorker,
    InMemoryArtifactStore,
    InMemoryCheckpointStore,
    InMemoryDeadLetterQueue,
    InMemoryExecutionStore,
    InMemoryLeaseManager,
    JobState,
    WorkerJob,
)


@pytest.mark.asyncio
async def test_inline_worker_lifecycle() -> None:
    """The inline worker should accept, claim, and finish jobs."""
    worker = InlineWorker()
    await worker.start()
    job = await worker.submit(
        WorkerJob(kind="fetch", payload={"url": "https://example.com"})
    )
    claimed = await worker.claim("worker-1")
    assert claimed is not None
    assert claimed.job_id == job.job_id
    assert claimed.state is JobState.RUNNING
    completed = await worker.complete(job.job_id)
    assert completed.state is JobState.SUCCEEDED
    await worker.heartbeat("worker-1", job.job_id)
    await worker.stop()


def test_in_memory_execution_store_records_runs() -> None:
    """The execution store should retain a run record in memory."""
    store = InMemoryExecutionStore()
    run_id = UUID("00000000-0000-0000-0000-000000000001")
    record = ExecutionRecord(run_id=run_id, outcome="succeeded", payload={"steps": 1})
    store.record(record)
    assert store.get(run_id) == record
    assert store.list() == [record]


def test_in_memory_checkpoint_store_round_trip() -> None:
    """The checkpoint store should preserve structured payloads."""
    store = InMemoryCheckpointStore()
    run_id = UUID("00000000-0000-0000-0000-000000000002")
    store.save(run_id, "fetch", {"url": "https://example.com"})
    assert store.load(run_id, "fetch") == {"url": "https://example.com"}
    store.delete(run_id, "fetch")
    assert store.load(run_id, "fetch") is None


def test_in_memory_artifact_store_round_trip() -> None:
    """The artifact store should round-trip bytes."""
    store = InMemoryArtifactStore()
    store.put_bytes("snapshot", b"payload")
    assert store.get_bytes("snapshot") == b"payload"
    store.delete("snapshot")
    assert store.get_bytes("snapshot") is None


def test_in_memory_lease_manager_round_trip() -> None:
    """The lease manager should issue and renew leases."""
    manager = InMemoryLeaseManager()
    run_id = UUID("00000000-0000-0000-0000-000000000003")
    lease = manager.acquire(run_id, "worker-1")
    renewed = manager.renew(lease)
    assert renewed.job_id == lease.job_id
    manager.release(renewed)


def test_in_memory_dead_letter_queue_round_trip_and_order() -> None:
    """The in-memory queue should match durable newest-first ordering."""
    from datetime import datetime, timedelta, timezone

    queue = InMemoryDeadLetterQueue()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = DeadLetterRecord(
        run_id=UUID("00000000-0000-0000-0000-000000000004"),
        pipeline_id="demo",
        step_id="step-1",
        reason="first",
        terminal_status="failed",
        created_at=base,
    )
    second = DeadLetterRecord(
        run_id=UUID("00000000-0000-0000-0000-000000000005"),
        pipeline_id="demo",
        step_id="step-2",
        reason="second",
        terminal_status="failed",
        created_at=base + timedelta(seconds=1),
    )
    queue.record(first)
    queue.record(second)
    assert queue.get(first.run_id) == first
    assert [record.run_id for record in queue.list()] == [second.run_id, first.run_id]
    assert queue.replay(second.run_id) == second
    assert queue.get(second.run_id) is None
