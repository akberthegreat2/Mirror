"""Tests for the SQLite scheduler backend."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mirror_core.scheduler import ScheduleRecord, SQLiteScheduler


def test_scheduler_import_is_stable() -> None:
    """Importing mirror_core.scheduler should not emit warnings."""
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import mirror_core.scheduler  # noqa: F401

        assert not caught


def test_sqlite_scheduler_round_trip(tmp_path: Path) -> None:
    """The SQLite scheduler should persist schedule entries and remain deterministic."""
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
