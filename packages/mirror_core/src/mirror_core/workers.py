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
    run_id: UUID | None = None
    pipeline_id: str | None = None
    step_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    state: JobState = JobState.QUEUED
    worker_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    lease_expires_at: datetime | None = None

    def model_post_init(self, __context: Any, /) -> None:
        if self.run_id is None:
            object.__setattr__(self, "run_id", self.job_id)
        if self.pipeline_id is None:
            object.__setattr__(
                self, "pipeline_id", self.metadata.get("pipeline_id", self.kind)
            )
        if self.step_id is None and self.metadata.get("step_id") is not None:
            object.__setattr__(self, "step_id", str(self.metadata["step_id"]))


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
    worker_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeadLetterRecord(BaseModel):
    """Structured terminal failure record for distributed execution."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    run_id: UUID
    pipeline_id: str
    step_id: str | None = None
    reason: str
    original_inputs: dict[str, Any] = Field(default_factory=dict)
    policy_state: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    retry_count: int = Field(default=0, ge=0)
    terminal_status: str
    worker_id: str | None = None
    lease_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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

    async def cancel(self, job_id: UUID, reason: str | None = None) -> WorkerJob:
        """Mark a job as cancelled."""
        ...

    def requeue_expired(self, *, now: datetime | None = None) -> list[WorkerJob]:
        """Requeue jobs whose leases have expired."""
        ...


@runtime_checkable
class ExecutionStore(Protocol):
    """Persistence contract for execution metadata."""

    def record(self, record: ExecutionRecord) -> None: ...

    def get(self, run_id: UUID) -> ExecutionRecord | None: ...

    def list(self) -> list[ExecutionRecord]: ...


@runtime_checkable
class DeadLetterQueue(Protocol):
    """Persistence contract for terminal failures."""

    def record(self, record: DeadLetterRecord) -> None: ...

    def get(self, run_id: UUID) -> DeadLetterRecord | None: ...

    def replay(self, run_id: UUID) -> DeadLetterRecord | None: ...

    def list(self) -> list[DeadLetterRecord]: ...


@runtime_checkable
class CheckpointStore(Protocol):
    """Persistence contract for resumable step checkpoints."""

    def save(self, run_id: UUID, step_id: str, payload: Mapping[str, Any]) -> None: ...

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None: ...

    def latest(self, run_id: UUID) -> tuple[str, dict[str, Any]] | None: ...

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

    def get(self, job_id: UUID) -> WorkerLease | None: ...

    def list(self) -> list[WorkerLease]: ...


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
        stored = job.model_copy(
            update={"state": JobState.QUEUED, "submitted_at": _utcnow()}
        )
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
            now = _utcnow()
            claimed = job.model_copy(
                update={
                    "state": JobState.RUNNING,
                    "worker_id": worker_id,
                    "claimed_at": now,
                    "lease_expires_at": now + timedelta(seconds=60),
                }
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
        completed = job.model_copy(
            update={
                "state": JobState.SUCCEEDED,
                "error": None,
                "completed_at": _utcnow(),
                "lease_expires_at": None,
            }
        )
        self._jobs_by_id[job_id] = completed
        return completed

    async def fail(self, job_id: UUID, error: str) -> WorkerJob:
        """Mark a job as failed."""
        self._ensure_started()
        job = self._require_job(job_id)
        failed = job.model_copy(
            update={
                "state": JobState.FAILED,
                "error": error,
                "completed_at": _utcnow(),
                "lease_expires_at": None,
            }
        )
        self._jobs_by_id[job_id] = failed
        return failed

    async def cancel(self, job_id: UUID, reason: str | None = None) -> WorkerJob:
        """Mark a job as cancelled."""
        self._ensure_started()
        job = self._require_job(job_id)
        cancelled = job.model_copy(
            update={
                "state": JobState.CANCELLED,
                "error": reason or job.error,
                "cancelled_at": _utcnow(),
                "lease_expires_at": None,
            }
        )
        self._jobs_by_id[job_id] = cancelled
        return cancelled

    def requeue_expired(self, *, now: datetime | None = None) -> list[WorkerJob]:
        """Requeue running jobs whose leases have expired."""
        self._ensure_started()
        now = _utcnow() if now is None else _utcnow() if now.tzinfo is None else now
        requeued: list[WorkerJob] = []
        for job in list(self._jobs_by_id.values()):
            if job.state is not JobState.RUNNING:
                continue
            if job.lease_expires_at is None or job.lease_expires_at > now:
                continue
            updated = job.model_copy(
                update={
                    "state": JobState.QUEUED,
                    "worker_id": None,
                    "claimed_at": None,
                    "lease_expires_at": None,
                }
            )
            self._jobs_by_id[job.job_id] = updated
            self._jobs.append(updated)
            requeued.append(updated)
        return requeued

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
        stored = job.model_copy(
            update={
                "state": JobState.QUEUED,
                "error": None,
                "submitted_at": now,
                "claimed_at": None,
                "completed_at": None,
                "cancelled_at": None,
                "lease_expires_at": None,
            }
        )
        conn = self._connection()
        conn.execute(
            """
            INSERT INTO jobs (
                job_id, kind, run_id, pipeline_id, step_id, payload, state, worker_id, error, metadata,
                created_at, updated_at, claimed_at, completed_at, cancelled_at, lease_expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id)
            DO UPDATE SET
                kind = excluded.kind,
                run_id = excluded.run_id,
                pipeline_id = excluded.pipeline_id,
                step_id = excluded.step_id,
                payload = excluded.payload,
                state = excluded.state,
                worker_id = excluded.worker_id,
                error = excluded.error,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at,
                claimed_at = excluded.claimed_at,
                completed_at = excluded.completed_at,
                cancelled_at = excluded.cancelled_at,
                lease_expires_at = excluded.lease_expires_at
            """,
            (
                str(stored.job_id),
                stored.kind,
                str(stored.run_id),
                stored.pipeline_id,
                stored.step_id,
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
            SET state = ?, worker_id = ?, updated_at = ?, claimed_at = ?, completed_at = NULL, cancelled_at = NULL, lease_expires_at = ?
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

    async def cancel(self, job_id: UUID, reason: str | None = None) -> WorkerJob:
        self._ensure_started()
        return self._transition(
            job_id, JobState.CANCELLED, error=reason, cancelled=True
        )

    def requeue_expired(self, *, now: datetime | None = None) -> list[WorkerJob]:
        """Move expired running jobs back to the queue."""
        self._ensure_started()
        conn = self._connection()
        now = _utcnow() if now is None else _utcnow() if now.tzinfo is None else now
        rows = conn.execute(
            "SELECT job_id FROM jobs WHERE state = ? AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?",
            (JobState.RUNNING.value, now.isoformat()),
        ).fetchall()
        requeued: list[WorkerJob] = []
        for row in rows:
            conn.execute(
                """
                UPDATE jobs
                SET state = ?, worker_id = NULL, updated_at = ?, claimed_at = NULL, completed_at = NULL, cancelled_at = NULL, lease_expires_at = NULL
                WHERE job_id = ?
                """,
                (JobState.QUEUED.value, now.isoformat(), row["job_id"]),
            )
            updated = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (row["job_id"],)
            ).fetchone()
            requeued.append(self._row_to_job(updated))
        conn.commit()
        return requeued

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
        self,
        job_id: UUID,
        state: JobState,
        *,
        error: str | None,
        cancelled: bool = False,
    ) -> WorkerJob:
        conn = self._connection()
        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (str(job_id),)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown job: {job_id}")
        updated_at = _utcnow().isoformat()
        completed_at = (
            updated_at
            if state in {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}
            else None
        )
        cancelled_at = updated_at if cancelled else None
        conn.execute(
            """
            UPDATE jobs
            SET state = ?, error = ?, updated_at = ?, completed_at = ?, cancelled_at = ?, lease_expires_at = NULL
            WHERE job_id = ?
            """,
            (state.value, error, updated_at, completed_at, cancelled_at, str(job_id)),
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
                run_id TEXT NOT NULL,
                pipeline_id TEXT NOT NULL,
                step_id TEXT,
                payload TEXT NOT NULL,
                state TEXT NOT NULL,
                worker_id TEXT,
                error TEXT,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_at TEXT,
                completed_at TEXT,
                cancelled_at TEXT,
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
            run_id=UUID(row["run_id"]),
            pipeline_id=row["pipeline_id"],
            step_id=row["step_id"],
            payload=json.loads(row["payload"]),
            state=JobState(row["state"]),
            worker_id=row["worker_id"],
            error=row["error"],
            metadata=json.loads(row["metadata"]),
            submitted_at=_parse_datetime(row["created_at"]),
            claimed_at=_parse_datetime(row["claimed_at"])
            if row["claimed_at"]
            else None,
            completed_at=_parse_datetime(row["completed_at"])
            if row["completed_at"]
            else None,
            cancelled_at=_parse_datetime(row["cancelled_at"])
            if row["cancelled_at"]
            else None,
            lease_expires_at=_parse_datetime(row["lease_expires_at"])
            if row["lease_expires_at"]
            else None,
        )


class SQLiteDeadLetterQueue:
    """SQLite-backed terminal failure queue for durable local workflows."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def record(self, record: DeadLetterRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO dead_letters(
                run_id, pipeline_id, step_id, reason, original_inputs,
                policy_state, provenance, retry_count, terminal_status, worker_id,
                lease_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                pipeline_id = excluded.pipeline_id,
                step_id = excluded.step_id,
                reason = excluded.reason,
                original_inputs = excluded.original_inputs,
                policy_state = excluded.policy_state,
                provenance = excluded.provenance,
                retry_count = excluded.retry_count,
                terminal_status = excluded.terminal_status,
                worker_id = excluded.worker_id,
                lease_id = excluded.lease_id,
                created_at = excluded.created_at
            """,
            (
                str(record.run_id),
                record.pipeline_id,
                record.step_id,
                record.reason,
                json.dumps(record.original_inputs, sort_keys=True),
                json.dumps(record.policy_state, sort_keys=True),
                json.dumps(record.provenance, sort_keys=True),
                record.retry_count,
                record.terminal_status,
                record.worker_id,
                record.lease_id,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, run_id: UUID) -> DeadLetterRecord | None:
        row = self._conn.execute(
            "SELECT * FROM dead_letters WHERE run_id = ?", (str(run_id),)
        ).fetchone()
        return None if row is None else self._row_to_record(row)

    def list(self) -> list[DeadLetterRecord]:
        rows = self._conn.execute(
            "SELECT * FROM dead_letters ORDER BY created_at, run_id"
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def replay(self, run_id: UUID) -> DeadLetterRecord | None:
        record = self.get(run_id)
        if record is None:
            return None
        self._conn.execute("DELETE FROM dead_letters WHERE run_id = ?", (str(run_id),))
        self._conn.commit()
        return record

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dead_letters (
                run_id TEXT PRIMARY KEY,
                pipeline_id TEXT NOT NULL,
                step_id TEXT,
                reason TEXT NOT NULL,
                original_inputs TEXT NOT NULL,
                policy_state TEXT NOT NULL,
                provenance TEXT NOT NULL,
                retry_count INTEGER NOT NULL,
                terminal_status TEXT NOT NULL,
                worker_id TEXT,
                lease_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _row_to_record(self, row: sqlite3.Row) -> DeadLetterRecord:
        return DeadLetterRecord(
            run_id=UUID(row["run_id"]),
            pipeline_id=row["pipeline_id"],
            step_id=row["step_id"],
            reason=row["reason"],
            original_inputs=json.loads(row["original_inputs"]),
            policy_state=json.loads(row["policy_state"]),
            provenance=json.loads(row["provenance"]),
            retry_count=row["retry_count"],
            terminal_status=row["terminal_status"],
            worker_id=row["worker_id"],
            lease_id=row["lease_id"],
            created_at=_parse_datetime(row["created_at"]),
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
        self._latest: dict[UUID, str] = {}

    def save(self, run_id: UUID, step_id: str, payload: Mapping[str, Any]) -> None:
        """Persist a checkpoint snapshot."""
        self._checkpoints[(run_id, step_id)] = dict(payload)
        self._latest[run_id] = step_id

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None:
        """Load a checkpoint snapshot."""
        payload = self._checkpoints.get((run_id, step_id))
        return None if payload is None else dict(payload)

    def latest(self, run_id: UUID) -> tuple[str, dict[str, Any]] | None:
        """Return the most recently stored checkpoint for a run."""
        step_id = self._latest.get(run_id)
        if step_id is None:
            return None
        payload = self._checkpoints.get((run_id, step_id))
        return None if payload is None else (step_id, dict(payload))

    def delete(self, run_id: UUID, step_id: str) -> None:
        """Delete a checkpoint snapshot."""
        self._checkpoints.pop((run_id, step_id), None)
        if self._latest.get(run_id) == step_id:
            remaining = [
                candidate
                for (candidate_run_id, candidate), _ in self._checkpoints.items()
                if candidate_run_id == run_id
            ]
            if remaining:
                self._latest[run_id] = remaining[-1]
            else:
                self._latest.pop(run_id, None)


class SQLiteCheckpointStore:
    """SQLite-backed checkpoint store for durable resumable workflows."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def save(self, run_id: UUID, step_id: str, payload: Mapping[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO checkpoints(run_id, step_id, payload, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(run_id, step_id)
            DO UPDATE SET payload = excluded.payload,
                          created_at = excluded.created_at
            """,
            (
                str(run_id),
                step_id,
                json.dumps(_checkpoint_encode(payload), sort_keys=True),
                _utcnow().isoformat(),
            ),
        )
        self._conn.commit()

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM checkpoints WHERE run_id = ? AND step_id = ?",
            (str(run_id), step_id),
        ).fetchone()
        if row is None:
            return None
        return _checkpoint_decode(json.loads(row["payload"]))

    def latest(self, run_id: UUID) -> tuple[str, dict[str, Any]] | None:
        row = self._conn.execute(
            """
            SELECT step_id, payload
            FROM checkpoints
            WHERE run_id = ?
            ORDER BY created_at DESC, step_id DESC
            LIMIT 1
            """,
            (str(run_id),),
        ).fetchone()
        if row is None:
            return None
        return row["step_id"], _checkpoint_decode(json.loads(row["payload"]))

    def delete(self, run_id: UUID, step_id: str) -> None:
        self._conn.execute(
            "DELETE FROM checkpoints WHERE run_id = ? AND step_id = ?",
            (str(run_id), step_id),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                run_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(run_id, step_id)
            )
            """
        )
        self._conn.commit()


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


class InMemoryDeadLetterQueue:
    """In-memory terminal failure queue for tests and local development."""

    def __init__(self) -> None:
        self._records: dict[UUID, DeadLetterRecord] = {}

    def record(self, record: DeadLetterRecord) -> None:
        self._records[record.run_id] = record

    def get(self, run_id: UUID) -> DeadLetterRecord | None:
        return self._records.get(run_id)

    def replay(self, run_id: UUID) -> DeadLetterRecord | None:
        record = self._records.pop(run_id, None)
        return record

    def list(self) -> list[DeadLetterRecord]:
        return list(self._records.values())


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

    def get(self, job_id: UUID) -> WorkerLease | None:
        """Return a lease if present."""
        return self._leases.get(job_id)

    def list(self) -> list[WorkerLease]:
        """Return all stored leases."""
        return list(self._leases.values())

    def _expiry(self, ttl_seconds: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


__all__ = [
    "ArtifactStore",
    "CheckpointStore",
    "DeadLetterQueue",
    "DeadLetterRecord",
    "ExecutionRecord",
    "ExecutionStore",
    "InMemoryArtifactStore",
    "InMemoryCheckpointStore",
    "InMemoryDeadLetterQueue",
    "InMemoryExecutionStore",
    "InMemoryLeaseManager",
    "InlineWorker",
    "JobState",
    "LeaseManager",
    "SQLiteCheckpointStore",
    "SQLiteDeadLetterQueue",
    "SQLiteWorkerBackend",
    "WorkerBackend",
    "WorkerJob",
    "WorkerLease",
]
