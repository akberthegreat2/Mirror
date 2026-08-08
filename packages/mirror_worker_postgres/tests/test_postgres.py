from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from mirror_core.workers import JobState, WorkerJob
from mirror_worker_postgres import (
    PostgresCheckpointStore,
    PostgresDeadLetterQueue,
    PostgresExecutionStore,
    PostgresLeaseManager,
    PostgresMetadataStore,
    PostgresWorkerBackend,
)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("MIRROR_TEST_POSTGRES_DSN"),
    reason="set MIRROR_TEST_POSTGRES_DSN for live PostgreSQL integration",
)
async def test_postgres_worker_lifecycle() -> None:
    dsn = os.environ["MIRROR_TEST_POSTGRES_DSN"]
    backend = PostgresWorkerBackend(dsn, lease_seconds=2)
    await backend.start()
    try:
        job = await backend.submit(
            WorkerJob(kind="integration", execution_class="io", payload={"value": 1})
        )
        claimed = await backend.claim("worker-a", "io")
        assert claimed is not None
        assert claimed.job_id == job.job_id
        assert claimed.state is JobState.RUNNING
        assert await backend.claim("worker-b", "io") is None
        await backend.heartbeat("worker-a", job.job_id)
        assert await backend.get(job.job_id) is not None
        await backend.stop()
        backend = PostgresWorkerBackend(dsn, lease_seconds=1)
        await backend.start()
        recovered = await backend.claim("worker-b", "io")
        assert recovered is None
        await asyncio.sleep(1.2)
        requeued = backend.requeue_expired()
        assert requeued and requeued[0].job_id == job.job_id
        recovered = await backend.claim("worker-b", "io")
        assert recovered is not None
        await backend.complete(job.job_id)
        completed = await backend.complete(job.job_id)
        assert completed.state is JobState.SUCCEEDED
    finally:
        await backend.stop()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("MIRROR_TEST_POSTGRES_DSN"),
    reason="set MIRROR_TEST_POSTGRES_DSN for live PostgreSQL integration",
)
def test_postgres_durable_stores() -> None:
    dsn = os.environ["MIRROR_TEST_POSTGRES_DSN"]
    run_id = uuid4()
    execution = PostgresExecutionStore(dsn)
    checkpoints = PostgresCheckpointStore(dsn)
    dead_letters = PostgresDeadLetterQueue(dsn)
    metadata = PostgresMetadataStore(dsn)
    leases = PostgresLeaseManager(dsn)
    try:
        from mirror_core.metadata import MetadataRecord
        from mirror_core.workers import DeadLetterRecord, ExecutionRecord

        execution.record(
            ExecutionRecord(run_id=run_id, outcome="succeeded", payload={"x": 1})
        )
        assert execution.get(run_id) is not None
        checkpoints.save(run_id, "step-1", {"state": "done"})
        assert checkpoints.load(run_id, "step-1") == {"state": "done"}
        metadata.put(
            MetadataRecord(
                namespace="integration", key=str(run_id), payload={"ok": True}
            )
        )
        assert metadata.get("integration", str(run_id)) is not None
        dead_letters.record(
            DeadLetterRecord(
                run_id=run_id,
                pipeline_id="integration",
                reason="test",
                terminal_status="failed",
            )
        )
        assert dead_letters.get(run_id) is not None
        lease = leases.acquire(run_id, "worker-a", ttl_seconds=10)
        assert leases.get(run_id) == lease
        leases.release(lease)
    finally:
        execution.close()
        checkpoints.close()
        dead_letters.close()
        metadata.close()
        leases.close()
