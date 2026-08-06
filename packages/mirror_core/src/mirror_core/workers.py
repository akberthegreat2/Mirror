"""Worker contracts and persistence implementations for Mirror."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class JobState(str, Enum):
    """Lifecycle states for one submitted worker job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkerJob(BaseModel):
    """Immutable worker job payload."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    job_id: UUID = Field(default_factory=uuid4)
    kind: str = "generic"
    payload: dict[str, Any] = Field(default_factory=dict)
    state: JobState = JobState.QUEUED
    worker_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkerLease(BaseModel):
    """Lease granted to one worker for a submitted job."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    job_id: UUID
    worker_id: str
    expires_at: datetime


class ExecutionRecord(BaseModel):
    """Stored execution metadata for a completed run."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    run_id: UUID
    outcome: str
    payload: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class WorkerBackend(Protocol):
    """Backend contract for worker transports."""

    async def start(self) -> None:
        """Prepare the backend for job submission."""
        ...

    async def stop(self) -> None:
        """Release backend resources."""
        ...

    async def submit(self, job: WorkerJob) -> WorkerJob:
        """Submit a job and return its stored representation."""
        ...

    async def claim(self, worker_id: str) -> WorkerJob | None:
        """Claim the next queued job for a worker."""
        ...

    async def heartbeat(self, worker_id: str, job_id: UUID | None = None) -> None:
        """Mark a worker as alive for observability and leasing."""
        ...

    async def complete(self, job_id: UUID) -> WorkerJob:
        """Mark a job as completed."""
        ...

    async def fail(self, job_id: UUID, error: str) -> WorkerJob:
        """Mark a job as failed."""
        ...


@runtime_checkable
class ExecutionStore(Protocol):
    """Persistence contract for execution metadata."""

    def record(self, record: ExecutionRecord) -> None: ...

    def get(self, run_id: UUID) -> ExecutionRecord | None: ...

    def list(self) -> list[ExecutionRecord]: ...


@runtime_checkable
class CheckpointStore(Protocol):
    """Persistence contract for resumable step checkpoints."""

    def save(self, run_id: UUID, step_id: str, payload: Mapping[str, Any]) -> None: ...

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None: ...

    def delete(self, run_id: UUID, step_id: str) -> None: ...


@runtime_checkable
class ArtifactStore(Protocol):
    """Persistence contract for binary or large artifacts."""

    def put_bytes(self, key: str, payload: bytes) -> None: ...

    def get_bytes(self, key: str) -> bytes | None: ...

    def delete(self, key: str) -> None: ...


@runtime_checkable
class LeaseManager(Protocol):
    """Lease contract used to coordinate workers."""

    def acquire(
        self, job_id: UUID, worker_id: str, ttl_seconds: int = 60
    ) -> WorkerLease: ...

    def renew(self, lease: WorkerLease, ttl_seconds: int = 60) -> WorkerLease: ...

    def release(self, lease: WorkerLease) -> None: ...


class InlineWorker:
    """In-memory worker backend for development and tests."""

    def __init__(self) -> None:
        self._jobs: deque[WorkerJob] = deque()
        self._jobs_by_id: dict[UUID, WorkerJob] = {}
        self._started = False
        self._heartbeats: list[tuple[str, UUID | None]] = []

    async def start(self) -> None:
        """Mark the backend as ready to accept jobs."""
        self._started = True

    async def stop(self) -> None:
        """Mark the backend as stopped."""
        self._started = False

    async def submit(self, job: WorkerJob) -> WorkerJob:
        """Enqueue a new job."""
        self._ensure_started()
        stored = job.model_copy(update={"state": JobState.QUEUED})
        self._jobs.append(stored)
        self._jobs_by_id[stored.job_id] = stored
        return stored

    async def claim(self, worker_id: str) -> WorkerJob | None:
        """Claim the next queued job for a worker."""
        self._ensure_started()
        while self._jobs:
            job = self._jobs.popleft()
            if job.state is not JobState.QUEUED:
                continue
            claimed = job.model_copy(
                update={"state": JobState.RUNNING, "worker_id": worker_id}
            )
            self._jobs_by_id[claimed.job_id] = claimed
            return claimed
        return None

    async def heartbeat(self, worker_id: str, job_id: UUID | None = None) -> None:
        """Record a worker heartbeat."""
        self._ensure_started()
        self._heartbeats.append((worker_id, job_id))

    async def complete(self, job_id: UUID) -> WorkerJob:
        """Mark a job as succeeded."""
        self._ensure_started()
        job = self._require_job(job_id)
        completed = job.model_copy(update={"state": JobState.SUCCEEDED, "error": None})
        self._jobs_by_id[job_id] = completed
        return completed

    async def fail(self, job_id: UUID, error: str) -> WorkerJob:
        """Mark a job as failed."""
        self._ensure_started()
        job = self._require_job(job_id)
        failed = job.model_copy(update={"state": JobState.FAILED, "error": error})
        self._jobs_by_id[job_id] = failed
        return failed

    @property
    def jobs(self) -> list[WorkerJob]:
        """Return the current in-memory queue snapshot."""
        return list(self._jobs_by_id.values())

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("Worker backend is not started")

    def _require_job(self, job_id: UUID) -> WorkerJob:
        try:
            return self._jobs_by_id[job_id]
        except KeyError as exc:
            raise KeyError(f"Unknown job: {job_id}") from exc


class SQLiteWorkerBackend:
    """SQLite-backed worker backend for durable local workflows.

    The backend stores jobs, state transitions, and heartbeats in a single
    SQLite database so local development and smoke tests exercise a
    production-like queue lifecycle without needing Redis or Celery.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._conn: sqlite3.Connection | None = None
        self._started = False

    async def start(self) -> None:
        if self._conn is None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self._path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._ensure_schema()
        self._started = True

    async def stop(self) -> None:
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None
        self._started = False

    async def submit(self, job: WorkerJob) -> WorkerJob:
        self._ensure_started()
        now = _utcnow()
        stored = job.model_copy(update={"state": JobState.QUEUED, "error": None})
        conn = self._connection()
        conn.execute(
            """
            INSERT INTO jobs (
                job_id, kind, payload, state, worker_id, error, metadata,
                created_at, updated_at, claimed_at, completed_at, lease_expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id)
            DO UPDATE SET
                kind = excluded.kind,
                payload = excluded.payload,
                state = excluded.state,
                worker_id = excluded.worker_id,
                error = excluded.error,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at,
                claimed_at = excluded.claimed_at,
                completed_at = excluded.completed_at,
                lease_expires_at = excluded.lease_expires_at
            """,
            (
                str(stored.job_id),
                stored.kind,
                json.dumps(stored.payload, sort_keys=True),
                stored.state.value,
                stored.worker_id,
                stored.error,
                json.dumps(stored.metadata, sort_keys=True),
                now.isoformat(),
                now.isoformat(),
                None,
                None,
                None,
            ),
        )
        conn.commit()
        return stored

    async def claim(self, worker_id: str) -> WorkerJob | None:
        self._ensure_started()
        conn = self._connection()
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE state = ?
            ORDER BY created_at, kind, job_id
            LIMIT 1
            """,
            (JobState.QUEUED.value,),
        ).fetchone()
        if row is None:
            conn.commit()
            return None
        claimed_at = _utcnow()
        lease_expires_at = claimed_at + timedelta(seconds=60)
        conn.execute(
            """
            UPDATE jobs
            SET state = ?, worker_id = ?, updated_at = ?, claimed_at = ?, lease_expires_at = ?
            WHERE job_id = ?
            """,
            (
                JobState.RUNNING.value,
                worker_id,
                claimed_at.isoformat(),
                claimed_at.isoformat(),
                lease_expires_at.isoformat(),
                row["job_id"],
            ),
        )
        conn.commit()
        claimed = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (row["job_id"],)
        ).fetchone()
        return self._row_to_job(claimed)

    async def heartbeat(self, worker_id: str, job_id: UUID | None = None) -> None:
        self._ensure_started()
        conn = self._connection()
        now = _utcnow()
        conn.execute(
            "INSERT INTO heartbeats(worker_id, job_id, at) VALUES (?, ?, ?)",
            (worker_id, str(job_id) if job_id is not None else None, now.isoformat()),
        )
        if job_id is not None:
            lease_expires_at = now + timedelta(seconds=60)
            conn.execute(
                """
                UPDATE jobs
                SET updated_at = ?, lease_expires_at = ?
                WHERE job_id = ?
                """,
                (now.isoformat(), lease_expires_at.isoformat(), str(job_id)),
            )
        conn.commit()

    async def complete(self, job_id: UUID) -> WorkerJob:
        self._ensure_started()
        return self._transition(job_id, JobState.SUCCEEDED, error=None)

    async def fail(self, job_id: UUID, error: str) -> WorkerJob:
        self._ensure_started()
        return self._transition(job_id, JobState.FAILED, error=error)

    @property
    def jobs(self) -> list[WorkerJob]:
        self._ensure_started()
        conn = self._connection()
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at, kind, job_id"
        ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        self._started = False

    def _transition(
        self, job_id: UUID, state: JobState, *, error: str | None
    ) -> WorkerJob:
        conn = self._connection()
        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (str(job_id),)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown job: {job_id}")
        updated_at = _utcnow().isoformat()
        completed_at = (
            updated_at if state in {JobState.SUCCEEDED, JobState.FAILED} else None
        )
        conn.execute(
            """
            UPDATE jobs
            SET state = ?, error = ?, updated_at = ?, completed_at = ?, lease_expires_at = NULL
            WHERE job_id = ?
            """,
            (state.value, error, updated_at, completed_at, str(job_id)),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (str(job_id),)
        ).fetchone()
        return self._row_to_job(updated)

    def _connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Worker backend is not started")
        return self._conn

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("Worker backend is not started")

    def _ensure_schema(self) -> None:
        conn = self._connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                state TEXT NOT NULL,
                worker_id TEXT,
                error TEXT,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_at TEXT,
                completed_at TEXT,
                lease_expires_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS heartbeats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT NOT NULL,
                job_id TEXT,
                at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_jobs_state_created ON jobs(state, created_at)"
        )
        conn.commit()

    def _row_to_job(self, row: sqlite3.Row | None) -> WorkerJob:
        if row is None:
            raise RuntimeError("Expected a job row")
        return WorkerJob(
            job_id=UUID(row["job_id"]),
            kind=row["kind"],
            payload=json.loads(row["payload"]),
            state=JobState(row["state"]),
            worker_id=row["worker_id"],
            error=row["error"],
            metadata=json.loads(row["metadata"]),
        )


class InMemoryExecutionStore:
    """In-memory execution metadata store for the alpha phase."""

    def __init__(self) -> None:
        self._records: dict[UUID, ExecutionRecord] = {}

    def record(self, record: ExecutionRecord) -> None:
        """Store a run record."""
        self._records[record.run_id] = record

    def get(self, run_id: UUID) -> ExecutionRecord | None:
        """Return a stored run record if present."""
        return self._records.get(run_id)

    def list(self) -> list[ExecutionRecord]:
        """Return all stored run records."""
        return list(self._records.values())


class InMemoryCheckpointStore:
    """In-memory checkpoint store for resumable development workflows."""

    def __init__(self) -> None:
        self._checkpoints: dict[tuple[UUID, str], dict[str, Any]] = {}

    def save(self, run_id: UUID, step_id: str, payload: Mapping[str, Any]) -> None:
        """Persist a checkpoint snapshot."""
        self._checkpoints[(run_id, step_id)] = dict(payload)

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None:
        """Load a checkpoint snapshot."""
        payload = self._checkpoints.get((run_id, step_id))
        return None if payload is None else dict(payload)

    def delete(self, run_id: UUID, step_id: str) -> None:
        """Delete a checkpoint snapshot."""
        self._checkpoints.pop((run_id, step_id), None)


class InMemoryArtifactStore:
    """In-memory artifact store for small development payloads."""

    def __init__(self) -> None:
        self._artifacts: dict[str, bytes] = {}

    def put_bytes(self, key: str, payload: bytes) -> None:
        """Store an artifact payload under a stable key."""
        self._artifacts[key] = bytes(payload)

    def get_bytes(self, key: str) -> bytes | None:
        """Return an artifact payload if present."""
        payload = self._artifacts.get(key)
        return None if payload is None else bytes(payload)

    def delete(self, key: str) -> None:
        """Delete an artifact payload."""
        self._artifacts.pop(key, None)


class InMemoryLeaseManager:
    """In-memory lease manager for single-process development."""

    def __init__(self) -> None:
        self._leases: dict[UUID, WorkerLease] = {}

    def acquire(
        self, job_id: UUID, worker_id: str, ttl_seconds: int = 60
    ) -> WorkerLease:
        """Acquire a lease for one job."""
        lease = WorkerLease(
            job_id=job_id,
            worker_id=worker_id,
            expires_at=self._expiry(ttl_seconds),
        )
        self._leases[job_id] = lease
        return lease

    def renew(self, lease: WorkerLease, ttl_seconds: int = 60) -> WorkerLease:
        """Renew an existing lease."""
        updated = lease.model_copy(update={"expires_at": self._expiry(ttl_seconds)})
        self._leases[lease.job_id] = updated
        return updated

    def release(self, lease: WorkerLease) -> None:
        """Release a lease."""
        self._leases.pop(lease.job_id, None)

    def _expiry(self, ttl_seconds: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


__all__ = [
    "ArtifactStore",
    "CheckpointStore",
    "ExecutionRecord",
    "ExecutionStore",
    "InMemoryArtifactStore",
    "InMemoryCheckpointStore",
    "InMemoryExecutionStore",
    "InMemoryLeaseManager",
    "InlineWorker",
    "JobState",
    "LeaseManager",
    "SQLiteWorkerBackend",
    "WorkerBackend",
    "WorkerJob",
    "WorkerLease",
]
