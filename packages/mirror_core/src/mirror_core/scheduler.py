"""Stable scheduling contracts and local persistence implementations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ScheduleState(str, Enum):
    """Lifecycle states for a scheduled job."""

    SCHEDULED = "scheduled"
    PAUSED = "paused"
    RUNNING = "running"
    DONE = "done"


class ScheduleRecord(BaseModel):
    """Immutable scheduled job record."""

    model_config = ConfigDict(frozen=True)

    schedule_id: UUID = Field(default_factory=uuid4)
    name: str
    due_at: datetime
    interval_seconds: float | None = Field(default=None, gt=0.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    state: ScheduleState = ScheduleState.SCHEDULED
    last_run_at: datetime | None = None


@runtime_checkable
class SchedulerBackend(Protocol):
    """Persistence and due-job contract for schedulers."""

    def schedule(self, record: ScheduleRecord) -> ScheduleRecord: ...

    def due(self, now: datetime | None = None) -> list[ScheduleRecord]: ...

    def mark_run(
        self, schedule_id: UUID, *, ran_at: datetime | None = None
    ) -> ScheduleRecord: ...

    def pause(self, schedule_id: UUID) -> ScheduleRecord: ...

    def resume(self, schedule_id: UUID) -> ScheduleRecord: ...

    def list(self) -> list[ScheduleRecord]: ...


class InMemoryScheduler:
    """In-memory scheduler for development and tests."""

    def __init__(self) -> None:
        self._records: dict[UUID, ScheduleRecord] = {}

    def schedule(self, record: ScheduleRecord) -> ScheduleRecord:
        self._records[record.schedule_id] = record
        return record

    def due(self, now: datetime | None = None) -> list[ScheduleRecord]:
        now = now or datetime.now(timezone.utc)
        return sorted(
            [
                record
                for record in self._records.values()
                if record.state is ScheduleState.SCHEDULED and record.due_at <= now
            ],
            key=lambda record: (record.due_at, record.name, str(record.schedule_id)),
        )

    def mark_run(
        self, schedule_id: UUID, *, ran_at: datetime | None = None
    ) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(
            update={
                "last_run_at": ran_at or datetime.now(timezone.utc),
                "due_at": record.due_at
                + timedelta(seconds=record.interval_seconds or 0.0)
                if record.interval_seconds is not None
                else record.due_at,
                "state": ScheduleState.SCHEDULED
                if record.interval_seconds is not None
                else ScheduleState.DONE,
            }
        )
        self._records[schedule_id] = updated
        return updated

    def pause(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(update={"state": ScheduleState.PAUSED})
        self._records[schedule_id] = updated
        return updated

    def resume(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(update={"state": ScheduleState.SCHEDULED})
        self._records[schedule_id] = updated
        return updated

    def list(self) -> list[ScheduleRecord]:
        return sorted(
            self._records.values(),
            key=lambda record: (record.due_at, record.name, str(record.schedule_id)),
        )

    def _require(self, schedule_id: UUID) -> ScheduleRecord:
        try:
            return self._records[schedule_id]
        except KeyError as exc:
            raise KeyError(f"Unknown schedule: {schedule_id}") from exc


class SQLiteScheduler:
    """SQLite-backed scheduler for durable local workflows."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
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
                record.last_run_at.isoformat()
                if record.last_run_at is not None
                else None,
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
            ORDER BY due_at, name, schedule_id
            """,
            (ScheduleState.SCHEDULED.value, now.isoformat()),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def mark_run(
        self, schedule_id: UUID, *, ran_at: datetime | None = None
    ) -> ScheduleRecord:
        record = self._require(schedule_id)
        updated = record.model_copy(
            update={
                "last_run_at": ran_at or datetime.now(timezone.utc),
                "due_at": record.due_at
                + timedelta(seconds=record.interval_seconds or 0.0)
                if record.interval_seconds is not None
                else record.due_at,
                "state": ScheduleState.SCHEDULED
                if record.interval_seconds is not None
                else ScheduleState.DONE,
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
        rows = self._conn.execute(
            "SELECT * FROM schedules ORDER BY due_at, name, schedule_id"
        ).fetchall()
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
            due_at=_parse_datetime(row["due_at"]),
            interval_seconds=row["interval_seconds"],
            payload=json.loads(row["payload"]),
            state=ScheduleState(row["state"]),
            last_run_at=_parse_datetime(row["last_run_at"])
            if row["last_run_at"]
            else None,
        )


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


__all__ = [
    "InMemoryScheduler",
    "SQLiteScheduler",
    "ScheduleRecord",
    "ScheduleState",
    "SchedulerBackend",
]
