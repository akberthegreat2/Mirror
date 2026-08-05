"""Tests for the pre-beta SQLite scheduler backend."""

from __future__ import annotations

import warnings
from datetime import datetime, timezone
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    from mirror_core.beta.scheduler import SQLiteScheduler

from mirror_core.scheduler import ScheduleRecord


def test_beta_module_warns_on_import() -> None:
    """Importing mirror_core.beta must surface a FutureWarning, not silence it."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import importlib

        import mirror_core.beta

        importlib.reload(mirror_core.beta)
        assert any(issubclass(w.category, FutureWarning) for w in caught)


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
