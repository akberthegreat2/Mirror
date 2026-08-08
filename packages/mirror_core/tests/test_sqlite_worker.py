"""Tests for the SQLite-backed worker backend."""

from __future__ import annotations

from pathlib import Path

import pytest
from mirror_core.workers import JobState, SQLiteWorkerBackend, WorkerJob


@pytest.mark.asyncio
async def test_sqlite_worker_backend_round_trip(tmp_path: Path) -> None:
    """The SQLite backend should persist, claim, and complete jobs."""
    backend = SQLiteWorkerBackend(tmp_path / "jobs.sqlite3")
    await backend.start()
    submitted = await backend.submit(WorkerJob(kind="crawl", payload={"url": "https://example.com"}))
    assert submitted.state is JobState.QUEUED
    claimed = await backend.claim("worker-1")
    assert claimed is not None
    assert claimed.job_id == submitted.job_id
    assert claimed.state is JobState.RUNNING
    completed = await backend.complete(submitted.job_id)
    assert completed.state is JobState.SUCCEEDED
    assert len(backend.jobs) == 1
    await backend.heartbeat("worker-1", submitted.job_id)
    await backend.stop()


@pytest.mark.asyncio
async def test_sqlite_worker_backend_cancel(tmp_path: Path) -> None:
    """The SQLite backend should support cooperative cancellation."""
    backend = SQLiteWorkerBackend(tmp_path / "jobs.sqlite3")
    await backend.start()
    submitted = await backend.submit(WorkerJob(kind="crawl", payload={"url": "https://example.com"}))
    cancelled = await backend.cancel(submitted.job_id, "requested")
    assert cancelled.state is JobState.CANCELLED
    assert cancelled.cancelled_at is not None
    await backend.stop()


def test_sqlite_checkpoint_store_round_trip_and_upsert(tmp_path: Path) -> None:
    """SQLite checkpoints must survive encoding, reopening, and upserts."""
    from uuid import UUID

    from mirror_core.workers import SQLiteCheckpointStore

    run_id = UUID("00000000-0000-0000-0000-000000000111")
    path = tmp_path / "checkpoints.sqlite3"
    store = SQLiteCheckpointStore(path)
    store.save(run_id, "step-1", {"count": 1, "nested": {"ok": True}})
    assert store.load(run_id, "step-1") == {"count": 1, "nested": {"ok": True}}
    store.save(run_id, "step-1", {"count": 2, "nested": {"ok": False}})
    assert store.load(run_id, "step-1") == {"count": 2, "nested": {"ok": False}}
    store.save(run_id, "step-2", {"count": 3})
    assert store.latest(run_id) == ("step-2", {"count": 3})
    store.delete(run_id, "step-1")
    assert store.load(run_id, "step-1") is None
    store.close()

    reopened = SQLiteCheckpointStore(path)
    assert reopened.latest(run_id) == ("step-2", {"count": 3})
    reopened.close()


def test_sqlite_dead_letter_queue_round_trip_order_and_replay(tmp_path: Path) -> None:
    """SQLite dead letters must persist, order newest-first, and replay once."""
    from datetime import datetime, timedelta, timezone
    from uuid import UUID

    from mirror_core.workers import DeadLetterRecord, SQLiteDeadLetterQueue

    first = UUID("00000000-0000-0000-0000-000000000121")
    second = UUID("00000000-0000-0000-0000-000000000122")
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    queue = SQLiteDeadLetterQueue(tmp_path / "dead-letters.sqlite3")
    queue.record(
        DeadLetterRecord(
            run_id=first,
            pipeline_id="crawl",
            reason="first",
            original_inputs={"url": "https://one.example"},
            policy_state={"retry": 1},
            provenance={"worker": "w1"},
            retry_count=1,
            terminal_status="failed",
            created_at=base,
        )
    )
    queue.record(
        DeadLetterRecord(
            run_id=second,
            pipeline_id="crawl",
            reason="second",
            original_inputs={"url": "https://two.example"},
            policy_state={"retry": 2},
            provenance={"worker": "w2"},
            retry_count=2,
            terminal_status="failed",
            created_at=base + timedelta(seconds=1),
        )
    )
    records = queue.list()
    assert [record.run_id for record in records] == [second, first]
    assert queue.get(second) is not None
    replayed = queue.replay(second)
    assert replayed is not None and replayed.reason == "second"
    assert queue.get(second) is None
    queue.close()

    reopened = SQLiteDeadLetterQueue(tmp_path / "dead-letters.sqlite3")
    assert [record.run_id for record in reopened.list()] == [first]
    reopened.close()
