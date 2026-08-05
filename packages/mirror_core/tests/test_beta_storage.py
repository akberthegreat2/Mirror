"""Tests for the pre-beta SQLite/filesystem storage backends."""

from __future__ import annotations

import warnings
from datetime import datetime, timezone
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    from mirror_core.beta.storage import FileSystemBlobStore, SQLiteMetadataStore

from mirror_core.storage import MetadataRecord


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


def test_filesystem_blob_store_round_trip(tmp_path: Path) -> None:
    """The filesystem blob store should round-trip bytes."""
    store = FileSystemBlobStore(tmp_path / "blobs")
    store.put_bytes("pages/index.html", b"<html></html>")
    assert store.get_bytes("pages/index.html") == b"<html></html>"
    store.delete("pages/index.html")
    assert store.get_bytes("pages/index.html") is None
