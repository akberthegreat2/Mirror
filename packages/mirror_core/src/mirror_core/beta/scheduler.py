"""Production-lean scheduler backend previewed ahead of the beta release.

The contract this implements (``SchedulerBackend``, ``ScheduleRecord``,
``ScheduleState``) lives in ``mirror_core.scheduler`` and is stable, frozen
core surface. This SQLite-backed implementation is not: see
``mirror_core.beta`` for what that status means.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from mirror_core.scheduler import ScheduleRecord, ScheduleState


class SQLiteScheduler:
    """SQLite-backed scheduler for local beta workflows."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def schedule(self, record: ScheduleRecord) -> ScheduleRecord:
        self._conn.execute(
            """
            INSERT INTO schedules(
                schedule_id, name, due_at, interval_seconds, payload, state, last_run_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(schedule_id)
            DO UPDATE SET name = excluded.name,
                          due_at = excluded.due_at,
                          interval_seconds = excluded.interval_seconds,
                          payload = excluded.payload,
                          state = excluded.state,
                          last_run_at = excluded.last_run_at
            """,
            (
                str(record.schedule_id),
                record.name,
                record.due_at.isoformat(),
                record.interval_seconds,
                json.dumps(record.payload, sort_keys=True),
                record.state.value,
                record.last_run_at.isoformat() if record.last_run_at is not None else None,
            ),
        )
        self._conn.commit()
        return record

    def due(self, now: datetime | None = None) -> list[ScheduleRecord]:
        now = now or datetime.now(timezone.utc)
        rows = self._conn.execute(
            """
            SELECT * FROM schedules
            WHERE state = ? AND due_at <= ?
            ORDER BY due_at, name
            """,
            (ScheduleState.SCHEDULED.value, now.isoformat()),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def mark_run(self, schedule_id: UUID, *, ran_at: datetime | None = None) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(
            update={
                "last_run_at": ran_at or datetime.now(timezone.utc),
                "due_at": record.due_at
                + timedelta(seconds=record.interval_seconds or 0.0)
                if record.interval_seconds is not None
                else record.due_at,
            }
        )
        self.schedule(updated)
        return updated

    def pause(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(update={"state": ScheduleState.PAUSED})
        self.schedule(updated)
        return updated

    def resume(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(update={"state": ScheduleState.SCHEDULED})
        self.schedule(updated)
        return updated

    def list(self) -> list[ScheduleRecord]:
        rows = self._conn.execute("SELECT * FROM schedules ORDER BY due_at, name").fetchall()
        return [self._row_to_record(row) for row in rows]

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                schedule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                due_at TEXT NOT NULL,
                interval_seconds REAL,
                payload TEXT NOT NULL,
                state TEXT NOT NULL,
                last_run_at TEXT
            )
            """
        )
        self._conn.commit()

    def _require(self, schedule_id: UUID) -> ScheduleRecord:
        row = self._conn.execute(
            "SELECT * FROM schedules WHERE schedule_id = ?",
            (str(schedule_id),),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown schedule: {schedule_id}")
        return self._row_to_record(row)

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ScheduleRecord:
        return ScheduleRecord(
            schedule_id=UUID(row["schedule_id"]),
            name=row["name"],
            due_at=datetime.fromisoformat(row["due_at"]),
            interval_seconds=row["interval_seconds"],
            payload=json.loads(row["payload"]),
            state=ScheduleState(row["state"]),
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
        )
