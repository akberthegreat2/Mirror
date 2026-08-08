"""Core-owned worker runtime helpers and durable backend stores."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from mirror_core.metadata import (
    MetadataRecord,
    MetadataStore,
    _decode_metadata_value,
    _encode_metadata_value,
)
from mirror_core.workers import (
    CheckpointStore,
    DeadLetterQueue,
    DeadLetterRecord,
    ExecutionRecord,
    ExecutionStore,
    LeaseManager,
    WorkerBackend,
    WorkerJob,
    WorkerLease,
)


class SQLiteExecutionStore:
    """SQLite-backed execution metadata store for worker outcomes."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def record(self, record: ExecutionRecord) -> None:
        """Store or update an execution record."""
        self._conn.execute(
            """
            INSERT INTO execution_runs(
                run_id, outcome, payload, worker_id, created_at, started_at,
                completed_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                outcome = excluded.outcome,
                payload = excluded.payload,
                worker_id = excluded.worker_id,
                created_at = excluded.created_at,
                started_at = excluded.started_at,
                completed_at = excluded.completed_at,
                metadata = excluded.metadata
            """,
            (
                str(record.run_id),
                record.outcome,
                json.dumps(_encode_metadata_value(record.payload), sort_keys=True),
                record.worker_id,
                record.created_at.isoformat(),
                record.started_at.isoformat() if record.started_at is not None else None,
                record.completed_at.isoformat() if record.completed_at is not None else None,
                json.dumps(_encode_metadata_value(record.metadata), sort_keys=True),
            ),
        )
        self._conn.commit()

    def get(self, run_id: UUID) -> ExecutionRecord | None:
        """Return one execution record if present."""
        row = self._conn.execute("SELECT * FROM execution_runs WHERE run_id = ?", (str(run_id),)).fetchone()
        return None if row is None else self._row_to_record(row)

    def list(self) -> list[ExecutionRecord]:
        """Return all stored execution records."""
        rows = self._conn.execute("SELECT * FROM execution_runs ORDER BY created_at, run_id").fetchall()
        return [self._row_to_record(row) for row in rows]

    def close(self) -> None:
        """Close the SQLite connection."""
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_runs (
                run_id TEXT PRIMARY KEY,
                outcome TEXT NOT NULL,
                payload TEXT NOT NULL,
                worker_id TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                metadata TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ExecutionRecord:
        return ExecutionRecord(
            run_id=UUID(row["run_id"]),
            outcome=row["outcome"],
            payload=_decode_metadata_value(json.loads(row["payload"])),
            worker_id=row["worker_id"],
            created_at=_parse_datetime(row["created_at"]),
            started_at=_parse_datetime(row["started_at"]) if row["started_at"] else None,
            completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
            metadata=_decode_metadata_value(json.loads(row["metadata"])),
        )


class SQLiteLeaseManager:
    """SQLite-backed lease manager for durable local workflows."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def acquire(self, job_id: UUID, worker_id: str, ttl_seconds: int = 60) -> WorkerLease:
        """Acquire or replace a lease for a job."""
        lease = WorkerLease(
            job_id=job_id,
            worker_id=worker_id,
            expires_at=_utcnow() + timedelta(seconds=ttl_seconds),
        )
        self._conn.execute(
            """
            INSERT INTO leases(job_id, worker_id, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                worker_id = excluded.worker_id,
                expires_at = excluded.expires_at
            """,
            (str(job_id), worker_id, lease.expires_at.isoformat()),
        )
        self._conn.commit()
        return lease

    def renew(self, lease: WorkerLease, ttl_seconds: int = 60) -> WorkerLease:
        """Renew an existing lease."""
        updated = lease.model_copy(update={"expires_at": _utcnow() + timedelta(seconds=ttl_seconds)})
        self._conn.execute(
            """
            INSERT INTO leases(job_id, worker_id, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                worker_id = excluded.worker_id,
                expires_at = excluded.expires_at
            """,
            (str(updated.job_id), updated.worker_id, updated.expires_at.isoformat()),
        )
        self._conn.commit()
        return updated

    def release(self, lease: WorkerLease) -> None:
        """Release an existing lease."""
        self._conn.execute("DELETE FROM leases WHERE job_id = ?", (str(lease.job_id),))
        self._conn.commit()

    def get(self, job_id: UUID) -> WorkerLease | None:
        """Return a stored lease if present."""
        row = self._conn.execute(
            "SELECT job_id, worker_id, expires_at FROM leases WHERE job_id = ?",
            (str(job_id),),
        ).fetchone()
        if row is None:
            return None
        return WorkerLease(
            job_id=UUID(row["job_id"]),
            worker_id=row["worker_id"],
            expires_at=_parse_datetime(row["expires_at"]),
        )

    def list(self) -> list[WorkerLease]:
        """Return all active leases."""
        rows = self._conn.execute("SELECT job_id, worker_id, expires_at FROM leases ORDER BY expires_at, job_id").fetchall()
        return [
            WorkerLease(
                job_id=UUID(row["job_id"]),
                worker_id=row["worker_id"],
                expires_at=_parse_datetime(row["expires_at"]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leases (
                job_id TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()


class WorkerRuntime:
    """Core-owned coordination layer for worker backends and durable state."""

    def __init__(
        self,
        backend: WorkerBackend,
        *,
        execution_store: ExecutionStore | None = None,
        checkpoint_store: CheckpointStore | None = None,
        dead_letter_queue: DeadLetterQueue | None = None,
        metadata_store: MetadataStore | None = None,
        lease_manager: LeaseManager | None = None,
    ) -> None:
        self.backend = backend
        self.execution_store = execution_store
        self.checkpoint_store = checkpoint_store
        self.dead_letter_queue = dead_letter_queue
        self.metadata_store = metadata_store
        self.lease_manager = lease_manager

    async def start(self) -> None:
        """Start the underlying backend."""
        await self.backend.start()

    async def stop(self) -> None:
        """Stop the underlying backend."""
        await self.backend.stop()

    async def submit(self, job: WorkerJob) -> WorkerJob:
        """Submit a new worker job and persist the audit trail."""
        stored = await self.backend.submit(job)
        self._record(
            MetadataRecord.audit_event(
                stored.job_id,
                "worker.job.submitted",
                payload={
                    "kind": stored.kind,
                    "state": stored.state.value,
                    "run_id": str(stored.run_id),
                    "pipeline_id": stored.pipeline_id,
                    "step_id": stored.step_id,
                    "metadata": dict(stored.metadata),
                },
            )
        )
        return stored

    async def claim(self, worker_id: str, execution_class: str = "default") -> WorkerJob | None:
        """Claim the next queued job for a worker in one execution class."""
        job = await self.backend.claim(worker_id, execution_class)
        if job is None:
            self._record(
                MetadataRecord.worker(
                    worker_id,
                    payload={"state": "idle", "at": _utcnow().isoformat()},
                )
            )
            return None
        if self.lease_manager is not None:
            lease = self.lease_manager.acquire(job.job_id, worker_id)
            self._record(
                MetadataRecord.worker_lease(
                    job.job_id,
                    worker_id,
                    payload={"expires_at": lease.expires_at.isoformat()},
                )
            )
        self._record(
            MetadataRecord.worker(
                worker_id,
                payload={
                    "state": "running",
                    "job_id": str(job.job_id),
                    "run_id": str(job.run_id),
                    "pipeline_id": job.pipeline_id,
                    "step_id": job.step_id,
                    "kind": job.kind,
                },
            )
        )
        return job

    async def claim_job(self, job_id: UUID, worker_id: str) -> WorkerJob | None:
        """Claim one specific job through the backend contract."""
        job = await self.backend.claim_job(job_id, worker_id)
        if job is not None and self.lease_manager is not None:
            lease = self.lease_manager.acquire(job.job_id, worker_id)
            self._record(
                MetadataRecord.worker_lease(
                    job.job_id,
                    worker_id,
                    payload={"expires_at": lease.expires_at.isoformat()},
                )
            )
        return job

    async def heartbeat(self, worker_id: str, job_id: UUID | None = None) -> None:
        """Mark a worker as alive and refresh the lease if possible."""
        await self.backend.heartbeat(worker_id, job_id)
        if job_id is not None and self.lease_manager is not None:
            lease = self.lease_manager.get(job_id) if hasattr(self.lease_manager, "get") else None
            if lease is not None:
                renewed = self.lease_manager.renew(lease)
                self._record(
                    MetadataRecord.worker_lease(
                        job_id,
                        worker_id,
                        payload={"expires_at": renewed.expires_at.isoformat()},
                    )
                )
        self._record(
            MetadataRecord.worker(
                worker_id,
                payload={
                    "state": "heartbeat",
                    "job_id": str(job_id) if job_id is not None else None,
                    "at": _utcnow().isoformat(),
                },
            )
        )

    async def complete(self, job_id: UUID) -> WorkerJob:
        """Mark a job as completed and persist the execution record."""
        job = await self.backend.complete(job_id)
        self._release_lease(job)
        self._record_execution(job, outcome="succeeded")
        return job

    async def fail(self, job_id: UUID, error: str, *, terminal: bool = True) -> WorkerJob:
        """Mark a job as failed and optionally route it to the DLQ."""
        job = await self.backend.fail(job_id, error)
        self._release_lease(job)
        self._record_execution(job, outcome="failed", error=error)
        if terminal and self.dead_letter_queue is not None:
            self.dead_letter_queue.record(
                DeadLetterRecord(
                    run_id=job.run_id,
                    pipeline_id=job.pipeline_id or job.kind,
                    step_id=job.step_id or job.metadata.get("step_id"),
                    reason=error,
                    original_inputs=dict(job.payload),
                    policy_state=dict(job.metadata),
                    provenance={
                        "worker_id": job.worker_id,
                        "job_id": str(job.job_id),
                        "run_id": str(job.run_id),
                    },
                    retry_count=int(job.metadata.get("retry_count", 0) or 0),
                    terminal_status="failed",
                    worker_id=job.worker_id,
                    lease_id=str(job.job_id),
                )
            )
            self._record(
                MetadataRecord.audit_event(
                    job.job_id,
                    "worker.job.dead_lettered",
                    payload={
                        "kind": job.kind,
                        "error": error,
                        "worker_id": job.worker_id,
                        "run_id": str(job.run_id),
                        "pipeline_id": job.pipeline_id,
                        "step_id": job.step_id,
                    },
                )
            )
        return job

    async def cancel(self, job_id: UUID, reason: str | None = None) -> WorkerJob:
        """Cancel a job cooperatively."""
        job = await self.backend.cancel(job_id, reason)
        self._release_lease(job)
        self._record_execution(job, outcome="cancelled", error=reason)
        self._record(
            MetadataRecord.audit_event(
                job.job_id,
                "worker.job.cancelled",
                payload={
                    "kind": job.kind,
                    "reason": reason,
                    "worker_id": job.worker_id,
                    "run_id": str(job.run_id),
                    "pipeline_id": job.pipeline_id,
                    "step_id": job.step_id,
                },
            )
        )
        return job

    async def requeue_expired(self) -> list[WorkerJob]:
        """Requeue any jobs whose leases have expired."""
        jobs = self.backend.requeue_expired()
        for job in jobs:
            self._record(
                MetadataRecord.audit_event(
                    job.job_id,
                    "worker.job.requeued",
                    payload={"kind": job.kind, "worker_id": job.worker_id},
                )
            )
        return jobs

    def _release_lease(self, job: WorkerJob) -> None:
        if self.lease_manager is None:
            return
        lease = self.lease_manager.get(job.job_id) if hasattr(self.lease_manager, "get") else None
        if lease is not None:
            self.lease_manager.release(lease)

    def _record_execution(self, job: WorkerJob, *, outcome: str, error: str | None = None) -> None:
        if self.execution_store is not None:
            self.execution_store.record(
                ExecutionRecord(
                    run_id=job.run_id,
                    outcome=outcome,
                    payload=dict(job.payload),
                    worker_id=job.worker_id,
                    created_at=job.submitted_at,
                    started_at=job.claimed_at,
                    completed_at=job.completed_at or job.cancelled_at or _utcnow(),
                    metadata={
                        **dict(job.metadata),
                        **({"error": error} if error else {}),
                        "run_id": str(job.run_id),
                        "pipeline_id": job.pipeline_id,
                        "step_id": job.step_id,
                    },
                )
            )
        run_id = job.run_id or job.job_id
        self._record(
            MetadataRecord.execution_run(
                run_id,
                payload={
                    "kind": job.kind,
                    "outcome": outcome,
                    "worker_id": job.worker_id,
                    "error": error,
                    "run_id": str(job.run_id),
                    "pipeline_id": job.pipeline_id,
                    "step_id": job.step_id,
                    "metadata": dict(job.metadata),
                },
            )
        )

    def _record(self, record: MetadataRecord) -> None:
        if self.metadata_store is not None:
            self.metadata_store.put(record)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


__all__ = [
    "SQLiteExecutionStore",
    "SQLiteLeaseManager",
    "WorkerRuntime",
]
