"""Tests for metadata and blob storage contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mirror_core.beta.storage import (
    FileSystemBlobStore,
    InMemoryBlobStore,
    InMemoryMetadataStore,
    MetadataRecord,
    SQLiteMetadataStore,
)


def test_in_memory_metadata_store_round_trip() -> None:
    """The metadata store should preserve structured records in memory."""
    store = InMemoryMetadataStore()
    record = MetadataRecord(namespace="crawl.urls", key="https://example.com", payload={"depth": 0})
    store.put(record)
    assert store.get("crawl.urls", "https://example.com") == record
    assert store.list("crawl.urls") == [record]


def test_sqlite_metadata_store_round_trip(tmp_path: Path) -> None:
    """The SQLite metadata store should persist and reload structured records."""
    store = SQLiteMetadataStore(tmp_path / "metadata.sqlite3")
    record = MetadataRecord(
        namespace="crawl.urls",
        key="https://example.com/about",
        payload={"depth": 1},
        created_at=datetime.now(timezone.utc),
    )
    store.put(record)
    assert store.get("crawl.urls", "https://example.com/about") == record
    assert store.list() == [record]
    store.close()


def test_in_memory_blob_store_round_trip() -> None:
    """The in-memory blob store should round-trip bytes."""
    store = InMemoryBlobStore()
    store.put_bytes("pages/index.html", b"payload")
    assert store.get_bytes("pages/index.html") == b"payload"
    store.delete("pages/index.html")
    assert store.get_bytes("pages/index.html") is None


def test_filesystem_blob_store_round_trip(tmp_path: Path) -> None:
    """The filesystem blob store should round-trip bytes."""
    store = FileSystemBlobStore(tmp_path / "blobs")
    store.put_bytes("pages/index.html", b"<html></html>")
    assert store.get_bytes("pages/index.html") == b"<html></html>"
    store.delete("pages/index.html")
    assert store.get_bytes("pages/index.html") is None
