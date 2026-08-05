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
