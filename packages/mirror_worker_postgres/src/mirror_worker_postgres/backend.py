"""PostgreSQL implementations of Mirror's durable worker contracts."""

from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from mirror_core.metadata import (
    MetadataRecord,
    MetadataStore,
    decode_metadata_value,
    encode_metadata_value,
)
from mirror_core.workers import (
    ArtifactStore,
    CheckpointStore,
    DeadLetterQueue,
    DeadLetterRecord,
    ExecutionRecord,
    ExecutionStore,
    JobState,
    LeaseManager,
    WorkerBackend,
    WorkerJob,
    WorkerLease,
)


_MIGRATION = Path(__file__).with_name("migrations") / "001_initial.sql"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dt(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


class _PostgresConnection:
    """Thread-safe synchronous connection used by core's synchronous stores."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._connection: psycopg.Connection[Any] | None = None
        self._lock = threading.RLock()

    def connect(self) -> None:
        with self._lock:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg.connect(self.dsn, row_factory=dict_row)
                self._connection.autocommit = True

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._lock:
            self.connect()
            assert self._connection is not None
            with self._connection.cursor() as cursor:
                cursor.execute(sql, params)
                if cursor.description is None:
                    return []
                return list(cursor.fetchall())


class PostgresWorkerBackend(WorkerBackend):
    """Durable PostgreSQL queue with transactional claim and lease recovery."""

    def __init__(self, dsn: str, *, lease_seconds: int = 60) -> None:
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        self.dsn = dsn
        self.lease_seconds = lease_seconds
        self._db = _PostgresConnection(dsn)
        self._started = False

    async def start(self) -> None:
        await asyncio.to_thread(self._start_sync)

    def _start_sync(self) -> None:
        self._db.connect()
        migration = _MIGRATION.read_text(encoding="utf-8")
        statements = [statement.strip() for statement in migration.split(";") if statement.strip()]
        for statement in statements:
            self._db.execute(statement)
        self._started = True

    async def stop(self) -> None:
        await asyncio.to_thread(self._db.close)
        self._started = False

    async def submit(self, job: WorkerJob) -> WorkerJob:
        self._ensure_started()
        stored = job.model_copy(
            update={
                "state": JobState.QUEUED,
                "error": None,
                "submitted_at": _utcnow(),
                "claimed_at": None,
                "completed_at": None,
                "cancelled_at": None,
                "lease_expires_at": None,
            }
        )
        await asyncio.to_thread(self._submit_sync, stored)
        return stored

    def _submit_sync(self, job: WorkerJob) -> None:
        self._db.execute(
            """
            INSERT INTO mirror_jobs(
                job_id, kind, run_id, pipeline_id, step_id, execution_class,
                payload, state, worker_id, error, metadata, submitted_at,
                claimed_at, completed_at, cancelled_at, lease_expires_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s)
            ON CONFLICT(job_id) DO UPDATE SET
                kind=EXCLUDED.kind, run_id=EXCLUDED.run_id, pipeline_id=EXCLUDED.pipeline_id,
                step_id=EXCLUDED.step_id, execution_class=EXCLUDED.execution_class,
                payload=EXCLUDED.payload, state=EXCLUDED.state, worker_id=EXCLUDED.worker_id,
                error=EXCLUDED.error, metadata=EXCLUDED.metadata, submitted_at=EXCLUDED.submitted_at,
                claimed_at=EXCLUDED.claimed_at, completed_at=EXCLUDED.completed_at,
                cancelled_at=EXCLUDED.cancelled_at, lease_expires_at=EXCLUDED.lease_expires_at
            """,
            (
                str(job.job_id), job.kind, str(job.run_id) if job.run_id else None,
                job.pipeline_id, job.step_id, job.execution_class,
                json.dumps(encode_metadata_value(job.payload)), job.state.value,
                job.worker_id, job.error, json.dumps(encode_metadata_value(job.metadata)),
                job.submitted_at, job.claimed_at, job.completed_at,
                job.cancelled_at, job.lease_expires_at,
            ),
        )

    async def get(self, job_id: UUID) -> WorkerJob | None:
        self._ensure_started()
        rows = await asyncio.to_thread(
            self._db.execute,
            "SELECT * FROM mirror_jobs WHERE job_id=%s",
            (str(job_id),),
        )
        return None if not rows else _job_from_row(rows[0])

    async def claim(self, worker_id: str, execution_class: str = "default") -> WorkerJob | None:
        self._ensure_started()
        rows = await asyncio.to_thread(self._claim_sync, worker_id, execution_class, None)
        return None if not rows else _job_from_row(rows[0])

    async def claim_job(self, job_id: UUID, worker_id: str) -> WorkerJob | None:
        self._ensure_started()
        rows = await asyncio.to_thread(self._claim_sync, worker_id, None, job_id)
        return None if not rows else _job_from_row(rows[0])

    def _claim_sync(
        self, worker_id: str, execution_class: str | None, job_id: UUID | None
    ) -> list[dict[str, Any]]:
        now = _utcnow()
        expires = now + timedelta(seconds=self.lease_seconds)
        class_filter = "AND execution_class = %s" if execution_class else ""
        id_filter = "AND job_id = %s" if job_id else ""
        params: list[Any] = [now]
        if execution_class:
            params.append(execution_class)
        if job_id:
            params.append(str(job_id))
        params.extend([worker_id, now, expires])
        with self._db._lock:
            self._db.connect()
            assert self._db._connection is not None
            connection = self._db._connection
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        WITH candidate AS (
                            SELECT job_id FROM mirror_jobs
                            WHERE state = 'queued'
                              AND (lease_expires_at IS NULL OR lease_expires_at <= %s)
                              {class_filter}
                              {id_filter}
                            ORDER BY submitted_at, job_id
                            FOR UPDATE SKIP LOCKED
                            LIMIT 1
                        )
                        UPDATE mirror_jobs AS j
                        SET state='running', worker_id=%s, claimed_at=%s, lease_expires_at=%s
                        FROM candidate
                        WHERE j.job_id = candidate.job_id
                        RETURNING j.*
                        """,
                        tuple(params),
                    )
                    if cursor.description is None:
                        return []
                    return list(cursor.fetchall())

    async def heartbeat(self, worker_id: str, job_id: UUID | None = None) -> None:
        self._ensure_started()
        await asyncio.to_thread(self._heartbeat_sync, worker_id, job_id)

    def _heartbeat_sync(self, worker_id: str, job_id: UUID | None) -> None:
        expires = _utcnow() + timedelta(seconds=self.lease_seconds)
        if job_id is None:
            self._db.execute(
                "INSERT INTO mirror_worker_heartbeats(worker_id, heartbeat_at) VALUES (%s,%s) ON CONFLICT(worker_id) DO UPDATE SET heartbeat_at=EXCLUDED.heartbeat_at",
                (worker_id, _utcnow()),
            )
            return
        self._db.execute(
            "UPDATE mirror_jobs SET lease_expires_at=%s WHERE job_id=%s AND state='running' AND worker_id=%s",
            (expires, str(job_id), worker_id),
        )
        self._db.execute(
            "INSERT INTO mirror_worker_heartbeats(worker_id, heartbeat_at) VALUES (%s,%s) ON CONFLICT(worker_id) DO UPDATE SET heartbeat_at=EXCLUDED.heartbeat_at",
            (worker_id, _utcnow()),
        )

    async def complete(self, job_id: UUID) -> WorkerJob:
        return await self._transition(job_id, JobState.SUCCEEDED, None)

    async def fail(self, job_id: UUID, error: str) -> WorkerJob:
        return await self._transition(job_id, JobState.FAILED, error)

    async def cancel(self, job_id: UUID, reason: str | None = None) -> WorkerJob:
        return await self._transition(job_id, JobState.CANCELLED, reason)

    async def _transition(self, job_id: UUID, state: JobState, error: str | None) -> WorkerJob:
        self._ensure_started()
        rows = await asyncio.to_thread(
            self._db.execute,
            """
            UPDATE mirror_jobs SET state=%s, error=%s, completed_at=%s,
                cancelled_at=CASE WHEN %s='cancelled' THEN %s ELSE cancelled_at END,
                lease_expires_at=NULL
            WHERE job_id=%s AND state='running'
            RETURNING *
            """,
            (state.value, error, _utcnow(), state.value, _utcnow(), str(job_id)),
        )
        if not rows:
            raise RuntimeError(f"Job {job_id} is not running or does not exist")
        return _job_from_row(rows[0])

    def requeue_expired(self, *, now: datetime | None = None) -> list[WorkerJob]:
        self._ensure_started()
        now = now or _utcnow()
        rows = self._db.execute(
            """
            UPDATE mirror_jobs SET state='queued', worker_id=NULL, claimed_at=NULL, lease_expires_at=NULL
            WHERE state='running' AND lease_expires_at IS NOT NULL AND lease_expires_at <= %s
            RETURNING *
            """,
            (now,),
        )
        return [_job_from_row(row) for row in rows]

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("PostgreSQL worker backend is not started")


class PostgresExecutionStore(ExecutionStore):
    """PostgreSQL execution history store."""

    def __init__(self, dsn: str) -> None:
        self._db = _PostgresConnection(dsn)

    def record(self, record: ExecutionRecord) -> None:
        self._db.execute(
            """
            INSERT INTO mirror_execution_runs(run_id,outcome,payload,worker_id,created_at,started_at,completed_at,metadata)
            VALUES (%s,%s,%s::jsonb,%s,%s,%s,%s,%s::jsonb)
            ON CONFLICT(run_id) DO UPDATE SET outcome=EXCLUDED.outcome,payload=EXCLUDED.payload,
              worker_id=EXCLUDED.worker_id,started_at=EXCLUDED.started_at,completed_at=EXCLUDED.completed_at,metadata=EXCLUDED.metadata
            """,
            (str(record.run_id), record.outcome, json.dumps(encode_metadata_value(record.payload)),
             record.worker_id, record.created_at, record.started_at, record.completed_at,
             json.dumps(encode_metadata_value(record.metadata))),
        )

    def get(self, run_id: UUID) -> ExecutionRecord | None:
        rows = self._db.execute("SELECT * FROM mirror_execution_runs WHERE run_id=%s", (str(run_id),))
        return None if not rows else _execution_from_row(rows[0])

    def list(self) -> list[ExecutionRecord]:
        return [_execution_from_row(row) for row in self._db.execute("SELECT * FROM mirror_execution_runs ORDER BY created_at, run_id")]

    def close(self) -> None:
        self._db.close()


class PostgresCheckpointStore(CheckpointStore):
    """PostgreSQL checkpoint store using JSONB snapshots."""

    def __init__(self, dsn: str) -> None:
        self._db = _PostgresConnection(dsn)

    def save(self, run_id: UUID, step_id: str, payload: dict[str, Any]) -> None:
        self._db.execute(
            "INSERT INTO mirror_checkpoints(run_id,step_id,payload,created_at) VALUES (%s,%s,%s::jsonb,%s) ON CONFLICT(run_id,step_id) DO UPDATE SET payload=EXCLUDED.payload,created_at=EXCLUDED.created_at",
            (str(run_id), step_id, json.dumps(encode_metadata_value(payload)), _utcnow()),
        )

    def load(self, run_id: UUID, step_id: str) -> dict[str, Any] | None:
        rows = self._db.execute("SELECT payload FROM mirror_checkpoints WHERE run_id=%s AND step_id=%s", (str(run_id), step_id))
        return None if not rows else decode_metadata_value(rows[0]["payload"])

    def latest(self, run_id: UUID) -> tuple[str, dict[str, Any]] | None:
        rows = self._db.execute("SELECT step_id,payload FROM mirror_checkpoints WHERE run_id=%s ORDER BY created_at DESC LIMIT 1", (str(run_id),))
        return None if not rows else (rows[0]["step_id"], decode_metadata_value(rows[0]["payload"]))

    def delete(self, run_id: UUID, step_id: str) -> None:
        self._db.execute("DELETE FROM mirror_checkpoints WHERE run_id=%s AND step_id=%s", (str(run_id), step_id))

    def close(self) -> None:
        self._db.close()


class PostgresArtifactStore(ArtifactStore):
    """PostgreSQL bytea artifact store for small durable artifacts."""

    def __init__(self, dsn: str) -> None:
        self._db = _PostgresConnection(dsn)

    def put_bytes(self, key: str, payload: bytes) -> None:
        self._db.execute("INSERT INTO mirror_artifacts(key,payload,created_at) VALUES (%s,%s,%s) ON CONFLICT(key) DO UPDATE SET payload=EXCLUDED.payload", (key, payload, _utcnow()))

    def get_bytes(self, key: str) -> bytes | None:
        rows = self._db.execute("SELECT payload FROM mirror_artifacts WHERE key=%s", (key,))
        return None if not rows else bytes(rows[0]["payload"])

    def delete(self, key: str) -> None:
        self._db.execute("DELETE FROM mirror_artifacts WHERE key=%s", (key,))

    def close(self) -> None:
        self._db.close()


class PostgresDeadLetterQueue(DeadLetterQueue):
    """Durable logical dead-letter store."""

    def __init__(self, dsn: str) -> None:
        self._db = _PostgresConnection(dsn)

    def record(self, record: DeadLetterRecord) -> None:
        self._db.execute(
            """
            INSERT INTO mirror_dead_letters(run_id,pipeline_id,step_id,reason,original_inputs,policy_state,provenance,retry_count,terminal_status,worker_id,lease_id,created_at)
            VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s)
            ON CONFLICT(run_id) DO UPDATE SET reason=EXCLUDED.reason,policy_state=EXCLUDED.policy_state,provenance=EXCLUDED.provenance,retry_count=EXCLUDED.retry_count,terminal_status=EXCLUDED.terminal_status,worker_id=EXCLUDED.worker_id,lease_id=EXCLUDED.lease_id
            """,
            (str(record.run_id), record.pipeline_id, record.step_id, record.reason,
             json.dumps(encode_metadata_value(record.original_inputs)), json.dumps(encode_metadata_value(record.policy_state)),
             json.dumps(encode_metadata_value(record.provenance)), record.retry_count, record.terminal_status,
             record.worker_id, record.lease_id, record.created_at),
        )

    def get(self, run_id: UUID) -> DeadLetterRecord | None:
        rows = self._db.execute("SELECT * FROM mirror_dead_letters WHERE run_id=%s", (str(run_id),))
        return None if not rows else _dead_letter_from_row(rows[0])

    def replay(self, run_id: UUID) -> DeadLetterRecord | None:
        return self.get(run_id)

    def list(self) -> list[DeadLetterRecord]:
        return [_dead_letter_from_row(row) for row in self._db.execute("SELECT * FROM mirror_dead_letters ORDER BY created_at, run_id")]

    def close(self) -> None:
        self._db.close()


class PostgresMetadataStore(MetadataStore):
    """PostgreSQL structured metadata store."""

    def __init__(self, dsn: str) -> None:
        self._db = _PostgresConnection(dsn)

    def put(self, record: MetadataRecord) -> None:
        self._db.execute(
            "INSERT INTO mirror_metadata(namespace,key,payload,created_at) VALUES (%s,%s,%s::jsonb,%s) ON CONFLICT(namespace,key) DO UPDATE SET payload=EXCLUDED.payload,created_at=EXCLUDED.created_at",
            (record.namespace, record.key, json.dumps(encode_metadata_value(record.payload)), record.created_at),
        )

    def get(self, namespace: str, key: str) -> MetadataRecord | None:
        rows = self._db.execute("SELECT * FROM mirror_metadata WHERE namespace=%s AND key=%s", (namespace, key))
        if not rows:
            return None
        row = rows[0]
        return MetadataRecord(namespace=row["namespace"], key=row["key"], payload=decode_metadata_value(row["payload"]), created_at=_dt(row["created_at"]) or _utcnow())

    def list(self, namespace: str | None = None) -> list[MetadataRecord]:
        if namespace is None:
            rows = self._db.execute("SELECT * FROM mirror_metadata ORDER BY namespace,key")
        else:
            rows = self._db.execute("SELECT * FROM mirror_metadata WHERE namespace=%s ORDER BY namespace,key", (namespace,))
        return [MetadataRecord(namespace=row["namespace"], key=row["key"], payload=decode_metadata_value(row["payload"]), created_at=_dt(row["created_at"]) or _utcnow()) for row in rows]

    def close(self) -> None:
        self._db.close()


class PostgresLeaseManager(LeaseManager):
    """PostgreSQL lease manager used as the authoritative lease record."""

    def __init__(self, dsn: str, *, ttl_seconds: int = 60) -> None:
        self._db = _PostgresConnection(dsn)
        self.ttl_seconds = ttl_seconds

    def acquire(self, job_id: UUID, worker_id: str, ttl_seconds: int = 60) -> WorkerLease:
        expires = _utcnow() + timedelta(seconds=ttl_seconds or self.ttl_seconds)
        rows = self._db.execute(
            """
            INSERT INTO mirror_leases(job_id,worker_id,expires_at)
            VALUES (%s,%s,%s)
            ON CONFLICT(job_id) DO UPDATE SET worker_id=EXCLUDED.worker_id, expires_at=EXCLUDED.expires_at
            WHERE mirror_leases.expires_at <= %s OR mirror_leases.worker_id = EXCLUDED.worker_id
            RETURNING job_id,worker_id,expires_at
            """,
            (str(job_id), worker_id, expires, _utcnow()),
        )
        if not rows:
            raise RuntimeError(f"Lease for {job_id} is currently owned by another live worker")
        return _lease_from_row(rows[0])

    def renew(self, lease: WorkerLease, ttl_seconds: int = 60) -> WorkerLease:
        expires = _utcnow() + timedelta(seconds=ttl_seconds or self.ttl_seconds)
        rows = self._db.execute("UPDATE mirror_leases SET expires_at=%s WHERE job_id=%s AND worker_id=%s RETURNING job_id,worker_id,expires_at", (expires, str(lease.job_id), lease.worker_id))
        if not rows:
            raise RuntimeError(f"Lease for {lease.job_id} is no longer owned by {lease.worker_id}")
        return _lease_from_row(rows[0])

    def release(self, lease: WorkerLease) -> None:
        self._db.execute("DELETE FROM mirror_leases WHERE job_id=%s AND worker_id=%s", (str(lease.job_id), lease.worker_id))

    def get(self, job_id: UUID) -> WorkerLease | None:
        rows = self._db.execute("SELECT job_id,worker_id,expires_at FROM mirror_leases WHERE job_id=%s", (str(job_id),))
        return None if not rows else _lease_from_row(rows[0])

    def list(self) -> list[WorkerLease]:
        return [_lease_from_row(row) for row in self._db.execute("SELECT job_id,worker_id,expires_at FROM mirror_leases ORDER BY expires_at,job_id")]

    def close(self) -> None:
        self._db.close()


def _job_from_row(row: dict[str, Any]) -> WorkerJob:
    return WorkerJob(
        job_id=UUID(str(row["job_id"])), kind=row["kind"],
        run_id=UUID(str(row["run_id"])) if row["run_id"] else None,
        pipeline_id=row["pipeline_id"], step_id=row["step_id"],
        execution_class=row["execution_class"], payload=decode_metadata_value(row["payload"]),
        state=JobState(row["state"]), worker_id=row["worker_id"], error=row["error"],
        metadata=decode_metadata_value(row["metadata"]), submitted_at=_dt(row["submitted_at"]) or _utcnow(),
        claimed_at=_dt(row["claimed_at"]), completed_at=_dt(row["completed_at"]),
        cancelled_at=_dt(row["cancelled_at"]), lease_expires_at=_dt(row["lease_expires_at"]),
    )


def _execution_from_row(row: dict[str, Any]) -> ExecutionRecord:
    return ExecutionRecord(run_id=UUID(str(row["run_id"])), outcome=row["outcome"], payload=decode_metadata_value(row["payload"]), worker_id=row["worker_id"], created_at=_dt(row["created_at"]) or _utcnow(), started_at=_dt(row["started_at"]), completed_at=_dt(row["completed_at"]), metadata=decode_metadata_value(row["metadata"]))


def _dead_letter_from_row(row: dict[str, Any]) -> DeadLetterRecord:
    return DeadLetterRecord(run_id=UUID(str(row["run_id"])), pipeline_id=row["pipeline_id"], step_id=row["step_id"], reason=row["reason"], original_inputs=decode_metadata_value(row["original_inputs"]), policy_state=decode_metadata_value(row["policy_state"]), provenance=decode_metadata_value(row["provenance"]), retry_count=row["retry_count"], terminal_status=row["terminal_status"], worker_id=row["worker_id"], lease_id=row["lease_id"], created_at=_dt(row["created_at"]) or _utcnow())


def _lease_from_row(row: dict[str, Any]) -> WorkerLease:
    return WorkerLease(job_id=UUID(str(row["job_id"])), worker_id=row["worker_id"], expires_at=_dt(row["expires_at"]) or _utcnow())
