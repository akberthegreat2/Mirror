"""Worker contracts and in-memory implementations for Mirror."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from enum import Enum
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

    def record(self, record: ExecutionRecord) -> None:
        ...

    def get(self, run_id: UUID) -> ExecutionRecord | None:
        ...

    def list(self) -> list[ExecutionRecord]:
        ...


@runtime_checkable
class CheckpointStore(Protocol):
    """Persistence contract for resumable step checkpoints."""

    def save(self, run_id: UUID, step_id: str, payload: Mapping[str, Any]) -> None:
        ...

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None:
        ...

    def delete(self, run_id: UUID, step_id: str) -> None:
        ...


@runtime_checkable
class ArtifactStore(Protocol):
    """Persistence contract for binary or large artifacts."""

    def put_bytes(self, key: str, payload: bytes) -> None:
        ...

    def get_bytes(self, key: str) -> bytes | None:
        ...

    def delete(self, key: str) -> None:
        ...


@runtime_checkable
class LeaseManager(Protocol):
    """Lease contract used to coordinate workers."""

    def acquire(self, job_id: UUID, worker_id: str, ttl_seconds: int = 60) -> WorkerLease:
        ...

    def renew(self, lease: WorkerLease, ttl_seconds: int = 60) -> WorkerLease:
        ...

    def release(self, lease: WorkerLease) -> None:
        ...


class InlineWorker:
    """In-memory worker backend for alpha development and tests."""

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
            claimed = job.model_copy(update={"state": JobState.RUNNING, "worker_id": worker_id})
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

    def acquire(self, job_id: UUID, worker_id: str, ttl_seconds: int = 60) -> WorkerLease:
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
