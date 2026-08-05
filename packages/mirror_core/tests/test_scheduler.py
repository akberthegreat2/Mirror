"""Tests for scheduler contracts and SQLite persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mirror_core.scheduler import (
    InMemoryScheduler,
    ScheduleRecord,
    ScheduleState,
    SQLiteScheduler,
)


def test_in_memory_scheduler_due_and_pause_resume() -> None:
    """The in-memory scheduler should track due jobs and state changes."""
    scheduler = InMemoryScheduler()
    due_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    record = ScheduleRecord(name="crawl", due_at=due_at, interval_seconds=60.0)
    scheduler.schedule(record)
    assert scheduler.due() == [record]

    paused = scheduler.pause(record.schedule_id)
    assert paused.state is ScheduleState.PAUSED
    assert scheduler.due() == []

    resumed = scheduler.resume(record.schedule_id)
    assert resumed.state is ScheduleState.SCHEDULED
    marked = scheduler.mark_run(record.schedule_id)
    assert marked.last_run_at is not None
    assert scheduler.list() == [marked]


def test_sqlite_scheduler_round_trip(tmp_path: Path) -> None:
    """The SQLite scheduler should persist schedule entries."""
    scheduler = SQLiteScheduler(tmp_path / "schedules.sqlite3")
    record = ScheduleRecord(name="crawl", due_at=datetime.now(timezone.utc))
    scheduler.schedule(record)
    assert scheduler.list() == [record]
    assert scheduler.due() == [record]
    scheduler.pause(record.schedule_id)
    assert scheduler.due() == []
    scheduler.resume(record.schedule_id)
    assert scheduler.due() == [record]
    scheduler.close()
