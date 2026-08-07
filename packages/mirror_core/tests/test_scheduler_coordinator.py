"""Tests for the core-owned scheduler coordinator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from mirror_core.metadata import InMemoryMetadataStore, MetadataNamespaces
from mirror_core.scheduler import (
    InMemoryScheduler,
    SchedulerCoordinator,
    ScheduleRecord,
    ScheduleTrigger,
    ScheduleTriggerKind,
)
from mirror_core.workers import InlineWorker


@pytest.mark.asyncio
async def test_scheduler_coordinator_dispatches_due_jobs() -> None:
    """Due schedules should be handed off to the worker backend."""
    scheduler = InMemoryScheduler()
    metadata_store = InMemoryMetadataStore()
    worker = InlineWorker()
    await worker.start()
    coordinator = SchedulerCoordinator(
        scheduler=scheduler,
        worker_backend=worker,
        metadata_store=metadata_store,
    )
    due_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    record = coordinator.schedule(
        ScheduleRecord(
            name="crawl",
            due_at=due_at,
            payload={"url": "https://example.com"},
            trigger=ScheduleTrigger(
                kind=ScheduleTriggerKind.INTERVAL, every_seconds=60
            ),
            queue_name="default",
        )
    )

    jobs = await coordinator.dispatch_due(now=due_at)

    assert len(jobs) == 1
    assert jobs[0].kind == "crawl"
    assert jobs[0].run_id == jobs[0].job_id
    assert jobs[0].pipeline_id == "crawl"
    assert jobs[0].payload["schedule_id"] == str(record.schedule_id)
    assert scheduler.due(now=due_at) == []

    stored = metadata_store.get(
        MetadataNamespaces.SCHEDULER_STATE, str(record.schedule_id)
    )
    assert stored is not None
    assert stored.payload["state"] == "scheduled"
    assert stored.payload["next_run_at"] is not None

    await worker.stop()


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("*/15 * * * *", datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc)),
        ("30 * * * *", datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc)),
    ],
)
def test_schedule_trigger_next_run(expression: str, expected: datetime) -> None:
    """Cron-like triggers should compute a deterministic next run."""
    record = ScheduleRecord(
        name="crawl",
        due_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        trigger=ScheduleTrigger(kind=ScheduleTriggerKind.CRON, expression=expression),
    )
    assert record.next_run(datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)) == expected
