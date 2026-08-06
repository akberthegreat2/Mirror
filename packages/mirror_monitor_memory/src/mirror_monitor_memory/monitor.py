"""Change-monitoring helpers with durable local storage."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import httpx
from mirror_monitor.models import MonitorSnapshot


class MonitorStateStore(Protocol):
    def get(self, url: str) -> str | None: ...
    def set(self, url: str, digest: str) -> None: ...


class MemoryMonitorStateStore:
    def __init__(self) -> None:
        self._state: dict[str, str] = {}

    def get(self, url: str) -> str | None:
        return self._state.get(url)

    def set(self, url: str, digest: str) -> None:
        self._state[url] = digest


class SQLiteMonitorStateStore:
    """Persist monitor state in SQLite for small durable deployments."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS monitor_state (
                    url TEXT PRIMARY KEY,
                    digest TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def get(self, url: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT digest FROM monitor_state WHERE url = ?", (url,)
            ).fetchone()
        return row[0] if row else None

    def set(self, url: str, digest: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO monitor_state(url, digest, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET digest = excluded.digest, updated_at = excluded.updated_at
                """,
                (url, digest, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()


class ContentMonitor:
    """Track page changes using content hashes and persisted state."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        user_agent: str = "MirrorWebInfra/1.0",
        state_store: MonitorStateStore | None = None,
    ) -> None:
        self._client = client
        self._user_agent = user_agent
        self._state_store = state_store or MemoryMonitorStateStore()

    async def check(self, url: str) -> MonitorSnapshot:
        async with self._managed_client() as client:
            response = await client.get(url, headers={"User-Agent": self._user_agent})
            body_sha256 = hashlib.sha256(response.content).hexdigest()
            previous_sha256 = self._state_store.get(url)
            changed = previous_sha256 is None or previous_sha256 != body_sha256
            self._state_store.set(url, body_sha256)
            return MonitorSnapshot(
                url=str(response.url),
                fetched_at=datetime.now(timezone.utc),
                status_code=response.status_code,
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
                body_sha256=body_sha256,
                changed=changed,
                previous_sha256=previous_sha256,
            )

    def _managed_client(self):
        if self._client is not None:
            return _ClientManager(self._client)
        return httpx.AsyncClient(follow_redirects=True, timeout=20.0)


class _ClientManager:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
