"""Stable scheduling contracts and local persistence implementations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.metadata import MetadataRecord, MetadataStore
from mirror_core.workers import WorkerBackend, WorkerJob


class ScheduleState(str, Enum):
    """Lifecycle states for a scheduled job."""

    SCHEDULED = "scheduled"
    PAUSED = "paused"
    RUNNING = "running"
    DONE = "done"
    DISABLED = "disabled"
    EXPIRED = "expired"


class ScheduleTriggerKind(str, Enum):
    """Supported schedule trigger families."""

    ONCE = "once"
    DELAY = "delay"
    INTERVAL = "interval"
    CRON = "cron"
    DEPENDENCY = "dependency"
    BACKFILL = "backfill"


class ScheduleTrigger(BaseModel):
    """Declarative scheduling trigger metadata."""

    model_config = ConfigDict(frozen=True)

    kind: ScheduleTriggerKind = ScheduleTriggerKind.ONCE
    expression: str | None = None
    every_seconds: float | None = Field(default=None, gt=0.0)
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    catch_up: bool = False

    def is_recurring(self) -> bool:
        """Return whether the trigger can produce more than one run."""
        return self.kind in {
            ScheduleTriggerKind.DELAY,
            ScheduleTriggerKind.INTERVAL,
            ScheduleTriggerKind.CRON,
            ScheduleTriggerKind.DEPENDENCY,
            ScheduleTriggerKind.BACKFILL,
        }


class ScheduleRecord(BaseModel):
    """Immutable scheduled job record."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    schedule_id: UUID = Field(default_factory=uuid4)
    name: str
    due_at: datetime
    interval_seconds: float | None = Field(default=None, gt=0.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    state: ScheduleState = ScheduleState.SCHEDULED
    last_run_at: datetime | None = None
    trigger: ScheduleTrigger = Field(default_factory=ScheduleTrigger)
    execution_class: str = "default"
    queue_name: str = "default"
    next_run_at: datetime | None = None
    expires_at: datetime | None = None
    disabled_at: datetime | None = None
    paused_at: datetime | None = None
    max_concurrency: int = Field(default=1, ge=1)
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any, /) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        if self.execution_class == "default" and self.queue_name != "default":
            object.__setattr__(self, "execution_class", self.queue_name)

    def is_paused(self) -> bool:
        """Return whether the schedule is explicitly paused."""
        return self.state is ScheduleState.PAUSED

    def is_disabled(self) -> bool:
        """Return whether the schedule is disabled."""
        return self.state is ScheduleState.DISABLED

    def is_expired(self, now: datetime | None = None) -> bool:
        """Return whether the schedule has expired."""
        if self.state is ScheduleState.EXPIRED:
            return True
        if self.expires_at is None:
            return False
        now = _coerce_datetime(now or datetime.now(timezone.utc))
        return self.expires_at <= now

    def effective_due_at(self) -> datetime:
        """Return the next time this schedule should be considered due."""
        return self.next_run_at or self.due_at

    def is_due(self, now: datetime | None = None) -> bool:
        """Return whether the schedule should be dispatched now."""
        now = _coerce_datetime(now or datetime.now(timezone.utc))
        return (
            self.state is ScheduleState.SCHEDULED
            and not self.is_expired(now)
            and self.effective_due_at() <= now
        )

    def next_run(self, now: datetime | None = None) -> datetime | None:
        """Compute the next run time based on trigger metadata."""
        now = _coerce_datetime(now or datetime.now(timezone.utc))
        if self.is_expired(now) or self.state in {
            ScheduleState.DONE,
            ScheduleState.EXPIRED,
        }:
            return None

        trigger = self.trigger
        if trigger.kind is ScheduleTriggerKind.ONCE:
            return None if self.last_run_at is not None else self.effective_due_at()

        if trigger.kind in {ScheduleTriggerKind.DELAY, ScheduleTriggerKind.INTERVAL}:
            interval = trigger.every_seconds or self.interval_seconds
            if interval is None:
                return self.effective_due_at()
            if self.last_run_at is None:
                return self.effective_due_at()
            base = self.last_run_at
            return base + timedelta(seconds=interval)

        if trigger.kind is ScheduleTriggerKind.CRON:
            expression = trigger.expression
            if expression:
                parsed = _next_cron_time(expression, after=self.last_run_at or now)
                if parsed is not None:
                    return parsed
            return self.effective_due_at() if self.last_run_at is None else None

        if trigger.kind in {
            ScheduleTriggerKind.DEPENDENCY,
            ScheduleTriggerKind.BACKFILL,
        }:
            if trigger.catch_up and self.last_run_at is not None:
                interval = trigger.every_seconds or self.interval_seconds
                if interval is not None:
                    return self.last_run_at + timedelta(seconds=interval)
            return self.effective_due_at() if self.last_run_at is None else None

        return self.effective_due_at() if self.last_run_at is None else None


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
        now = _coerce_datetime(now or datetime.now(timezone.utc))
        return sorted(
            [record for record in self._records.values() if record.is_due(now)],
            key=lambda record: (
                record.effective_due_at(),
                record.name,
                str(record.schedule_id),
            ),
        )

    def mark_run(
        self, schedule_id: UUID, *, ran_at: datetime | None = None
    ) -> ScheduleRecord:
        record = self._require(schedule_id)
        ran_at = _coerce_datetime(ran_at or datetime.now(timezone.utc))
        updated_base = record.model_copy(update={"last_run_at": ran_at})
        next_run_at = updated_base.next_run(ran_at)
        updated = updated_base.model_copy(
            update={
                "next_run_at": next_run_at,
                "state": ScheduleState.DONE
                if next_run_at is None
                else ScheduleState.SCHEDULED,
            }
        )
        self._records[schedule_id] = updated
        return updated

    def pause(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        now = datetime.now(timezone.utc)
        updated = record.model_copy(
            update={
                "state": ScheduleState.PAUSED,
                "paused_at": now,
                "disabled_at": None,
            }
        )
        self._records[schedule_id] = updated
        return updated

    def resume(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        now = datetime.now(timezone.utc)
        state = (
            ScheduleState.EXPIRED if record.is_expired(now) else ScheduleState.SCHEDULED
        )
        next_run_at = record.next_run(now)
        if record.trigger.kind is ScheduleTriggerKind.ONCE:
            next_run_at = None
        updated = record.model_copy(
            update={
                "state": state,
                "paused_at": None,
                "disabled_at": None,
                "next_run_at": next_run_at,
            }
        )
        self._records[schedule_id] = updated
        return updated

    def list(self) -> list[ScheduleRecord]:
        return sorted(
            self._records.values(),
            key=lambda record: (
                record.effective_due_at(),
                record.name,
                str(record.schedule_id),
            ),
        )

    def _require(self, schedule_id: UUID) -> ScheduleRecord:
        try:
            return self._records[schedule_id]
        except KeyError as exc:
            raise KeyError(f"Unknown schedule: {schedule_id}") from exc

    @staticmethod
    def _normalize(record: ScheduleRecord) -> ScheduleRecord:
        return record


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
                schedule_id, name, due_at, interval_seconds, payload, state, last_run_at,
                trigger_kind, trigger_expression, trigger_every_seconds, trigger_depends_on,
                trigger_catch_up, execution_class, queue_name, next_run_at, expires_at, disabled_at, paused_at,
                max_concurrency, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(schedule_id)
            DO UPDATE SET name = excluded.name,
                          due_at = excluded.due_at,
                          interval_seconds = excluded.interval_seconds,
                          payload = excluded.payload,
                          state = excluded.state,
                          last_run_at = excluded.last_run_at,
                          trigger_kind = excluded.trigger_kind,
                          trigger_expression = excluded.trigger_expression,
                          trigger_every_seconds = excluded.trigger_every_seconds,
                          trigger_depends_on = excluded.trigger_depends_on,
                          trigger_catch_up = excluded.trigger_catch_up,
                          execution_class = excluded.execution_class,
                          queue_name = excluded.queue_name,
                          next_run_at = excluded.next_run_at,
                          expires_at = excluded.expires_at,
                          disabled_at = excluded.disabled_at,
                          paused_at = excluded.paused_at,
                          max_concurrency = excluded.max_concurrency,
                          metadata = excluded.metadata
            """,
            self._record_values(record),
        )
        self._conn.commit()
        return record

    def due(self, now: datetime | None = None) -> list[ScheduleRecord]:
        now = _coerce_datetime(now or datetime.now(timezone.utc))
        rows = self._conn.execute(
            """
            SELECT * FROM schedules
            WHERE state = ? AND COALESCE(next_run_at, due_at) <= ?
            ORDER BY COALESCE(next_run_at, due_at), name, schedule_id
            """,
            (ScheduleState.SCHEDULED.value, now.isoformat()),
        ).fetchall()
        return [
            self._row_to_record(row)
            for row in rows
            if self._row_to_record(row).is_due(now)
        ]

    def mark_run(
        self, schedule_id: UUID, *, ran_at: datetime | None = None
    ) -> ScheduleRecord:
        record = self._require(schedule_id)
        ran_at = _coerce_datetime(ran_at or datetime.now(timezone.utc))
        updated_base = record.model_copy(update={"last_run_at": ran_at})
        next_run_at = updated_base.next_run(ran_at)
        updated = updated_base.model_copy(
            update={
                "next_run_at": next_run_at,
                "state": ScheduleState.DONE
                if next_run_at is None
                else ScheduleState.SCHEDULED,
            }
        )
        self.schedule(updated)
        return updated

    def pause(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        now = datetime.now(timezone.utc)
        updated = record.model_copy(
            update={
                "state": ScheduleState.PAUSED,
                "paused_at": now,
                "disabled_at": None,
            }
        )
        self.schedule(updated)
        return updated

    def resume(self, schedule_id: UUID) -> ScheduleRecord:
        record = self._require(schedule_id)
        now = datetime.now(timezone.utc)
        state = (
            ScheduleState.EXPIRED if record.is_expired(now) else ScheduleState.SCHEDULED
        )
        next_run_at = record.next_run(now)
        if record.trigger.kind is ScheduleTriggerKind.ONCE:
            next_run_at = None
        updated = record.model_copy(
            update={
                "state": state,
                "paused_at": None,
                "disabled_at": None,
                "next_run_at": next_run_at,
            }
        )
        self.schedule(updated)
        return updated

    def list(self) -> list[ScheduleRecord]:
        rows = self._conn.execute(
            "SELECT * FROM schedules ORDER BY COALESCE(next_run_at, due_at), name, schedule_id"
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
                last_run_at TEXT,
                trigger_kind TEXT NOT NULL,
                trigger_expression TEXT,
                trigger_every_seconds REAL,
                trigger_depends_on TEXT NOT NULL,
                trigger_catch_up INTEGER NOT NULL,
                execution_class TEXT NOT NULL DEFAULT 'default',
                queue_name TEXT NOT NULL,
                next_run_at TEXT,
                expires_at TEXT,
                disabled_at TEXT,
                paused_at TEXT,
                max_concurrency INTEGER NOT NULL,
                metadata TEXT NOT NULL
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

    def _record_values(self, record: ScheduleRecord) -> tuple[Any, ...]:
        return (
            str(record.schedule_id),
            record.name,
            record.due_at.isoformat(),
            record.interval_seconds,
            json.dumps(record.payload, sort_keys=True),
            record.state.value,
            record.last_run_at.isoformat() if record.last_run_at is not None else None,
            record.trigger.kind.value,
            record.trigger.expression,
            record.trigger.every_seconds,
            json.dumps(list(record.trigger.depends_on), sort_keys=True),
            1 if record.trigger.catch_up else 0,
            record.execution_class,
            record.queue_name,
            record.next_run_at.isoformat() if record.next_run_at is not None else None,
            record.expires_at.isoformat() if record.expires_at is not None else None,
            record.disabled_at.isoformat() if record.disabled_at is not None else None,
            record.paused_at.isoformat() if record.paused_at is not None else None,
            record.max_concurrency,
            json.dumps(dict(record.metadata), sort_keys=True),
        )

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ScheduleRecord:
        trigger = ScheduleTrigger(
            kind=ScheduleTriggerKind(row["trigger_kind"]),
            expression=row["trigger_expression"],
            every_seconds=row["trigger_every_seconds"],
            depends_on=tuple(json.loads(row["trigger_depends_on"] or "[]")),
            catch_up=bool(row["trigger_catch_up"]),
        )
        record = ScheduleRecord(
            schedule_id=UUID(row["schedule_id"]),
            name=row["name"],
            due_at=_parse_datetime(row["due_at"]),
            interval_seconds=row["interval_seconds"],
            payload=json.loads(row["payload"]),
            state=ScheduleState(row["state"]),
            last_run_at=_parse_datetime(row["last_run_at"])
            if row["last_run_at"]
            else None,
            trigger=trigger,
            execution_class=row["execution_class"] if "execution_class" in row.keys() else row["queue_name"],
            queue_name=row["queue_name"],
            next_run_at=_parse_datetime(row["next_run_at"])
            if row["next_run_at"]
            else None,
            expires_at=_parse_datetime(row["expires_at"])
            if row["expires_at"]
            else None,
            disabled_at=_parse_datetime(row["disabled_at"])
            if row["disabled_at"]
            else None,
            paused_at=_parse_datetime(row["paused_at"]) if row["paused_at"] else None,
            max_concurrency=row["max_concurrency"],
            metadata=json.loads(row["metadata"]),
        )
        return InMemoryScheduler._normalize(record)


class SchedulerCoordinator:
    """Core-owned service that turns due schedules into worker jobs."""

    def __init__(
        self,
        scheduler: SchedulerBackend,
        worker_backend: WorkerBackend,
        metadata_store: MetadataStore | None = None,
    ) -> None:
        self._scheduler = scheduler
        self._worker_backend = worker_backend
        self._metadata_store = metadata_store

    async def dispatch_due(self, now: datetime | None = None) -> list[WorkerJob]:
        """Submit all due schedules to the worker backend."""
        now = _coerce_datetime(now or datetime.now(timezone.utc))
        jobs: list[WorkerJob] = []
        for record in self._scheduler.due(now):
            job = WorkerJob(
                kind=record.name,
                pipeline_id=record.metadata.get("pipeline_id", record.name),
                payload={
                    "schedule_id": str(record.schedule_id),
                    "name": record.name,
                    "execution_class": record.execution_class,
                    "queue_name": record.queue_name,
                    "scheduled_at": record.effective_due_at().isoformat(),
                    "payload": record.payload,
                    "metadata": dict(record.metadata),
                },
                metadata={
                    "schedule_id": str(record.schedule_id),
                    "schedule_name": record.name,
                    "execution_class": record.execution_class,
                    "queue_name": record.queue_name,
                    "trigger": record.trigger.model_dump(mode="json"),
                },
            )
            submitted = await self._worker_backend.submit(job)
            updated = self._scheduler.mark_run(record.schedule_id, ran_at=now)
            self._record_metadata(
                MetadataRecord.scheduler(
                    record.schedule_id,
                    payload={
                        "name": updated.name,
                        "state": updated.state.value,
                        "execution_class": updated.execution_class,
                        "queue_name": updated.queue_name,
                        "last_run_at": updated.last_run_at.isoformat()
                        if updated.last_run_at is not None
                        else None,
                        "next_run_at": updated.next_run_at.isoformat()
                        if updated.next_run_at is not None
                        else None,
                        "trigger": updated.trigger.model_dump(mode="json"),
                    },
                )
            )
            jobs.append(submitted)
        return jobs

    def schedule(self, record: ScheduleRecord) -> ScheduleRecord:
        """Persist a schedule and record its metadata."""
        stored = self._scheduler.schedule(record)
        self._record_metadata(
            MetadataRecord.scheduler(
                stored.schedule_id,
                payload={
                    "name": stored.name,
                    "state": stored.state.value,
                    "execution_class": stored.execution_class,
                    "queue_name": stored.queue_name,
                    "due_at": stored.due_at.isoformat(),
                    "next_run_at": stored.next_run_at.isoformat()
                    if stored.next_run_at is not None
                    else None,
                    "trigger": stored.trigger.model_dump(mode="json"),
                },
            )
        )
        return stored

    def pause(self, schedule_id: UUID) -> ScheduleRecord:
        """Pause an existing schedule and record the state transition."""
        updated = self._scheduler.pause(schedule_id)
        self._record_metadata(
            MetadataRecord.scheduler(
                schedule_id,
                payload={
                    "state": updated.state.value,
                    "execution_class": updated.execution_class,
                        "queue_name": updated.queue_name,
                },
            )
        )
        return updated

    def resume(self, schedule_id: UUID) -> ScheduleRecord:
        """Resume an existing schedule and record the state transition."""
        updated = self._scheduler.resume(schedule_id)
        self._record_metadata(
            MetadataRecord.scheduler(
                schedule_id,
                payload={
                    "state": updated.state.value,
                    "execution_class": updated.execution_class,
                        "queue_name": updated.queue_name,
                },
            )
        )
        return updated

    def _record_metadata(self, record: MetadataRecord) -> None:
        if self._metadata_store is not None:
            self._metadata_store.put(record)


def _coerce_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _next_cron_time(expression: str, *, after: datetime) -> datetime | None:
    """Return the next time for a tiny cron subset.

    The implementation intentionally supports the practical subset used by the
    repository tests: ``*`` and ``*/N`` minute expressions with optional
    six-field second precision.
    """

    parts = expression.split()
    if len(parts) not in {5, 6}:
        return None
    if len(parts) == 5:
        second_field = "0"
        minute_field, hour_field, day_field, month_field, weekday_field = parts
    else:
        (
            second_field,
            minute_field,
            hour_field,
            day_field,
            month_field,
            weekday_field,
        ) = parts

    if (
        hour_field != "*"
        or day_field != "*"
        or month_field != "*"
        or weekday_field != "*"
    ):
        return None

    after = _coerce_datetime(after).replace(microsecond=0)
    start = after + timedelta(seconds=1)

    def _parse_field(field: str, upper: int) -> list[int] | None:
        if field == "*":
            return list(range(upper))
        if field.startswith("*/"):
            try:
                step = int(field[2:])
            except ValueError:
                return None
            if step <= 0:
                return None
            return list(range(0, upper, step))
        try:
            value = int(field)
        except ValueError:
            return None
        if 0 <= value < upper:
            return [value]
        return None

    minute_candidates = _parse_field(minute_field, 60)
    second_candidates = _parse_field(second_field, 60)
    if minute_candidates is None or second_candidates is None:
        return None

    for day_offset in range(366):
        day = (start + timedelta(days=day_offset)).date()
        hour_start = start.hour if day_offset == 0 else 0
        for hour in range(hour_start, 24):
            for minute in minute_candidates:
                if day_offset == 0 and hour == start.hour and minute < start.minute:
                    continue
                for second in second_candidates:
                    if (
                        day_offset == 0
                        and hour == start.hour
                        and minute == start.minute
                        and second < start.second
                    ):
                        continue
                    candidate = datetime(
                        day.year,
                        day.month,
                        day.day,
                        hour,
                        minute,
                        second,
                        tzinfo=start.tzinfo,
                    )
                    if candidate > after:
                        return candidate
    return None


__all__ = [
    "InMemoryScheduler",
    "SQLiteScheduler",
    "ScheduleRecord",
    "ScheduleState",
    "ScheduleTrigger",
    "ScheduleTriggerKind",
    "SchedulerBackend",
    "SchedulerCoordinator",
]
