"""Tests for the dedicated core metadata module."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import uuid4

import pytest
from mirror_core.metadata import (
    InMemoryMetadataStore,
    MetadataNamespaces,
    MetadataRecord,
    SQLiteMetadataStore,
    decode_metadata_value,
    encode_metadata_value,
    register_metadata_enum,
)
from mirror_core.storage import (
    MetadataRecord as StorageMetadataRecord,
)
from mirror_core.storage import (
    SQLiteMetadataStore as StorageSQLiteMetadataStore,
)


def test_storage_reexports_metadata_contracts() -> None:
    """The legacy storage import path should continue to expose metadata contracts."""
    assert StorageMetadataRecord is MetadataRecord
    assert StorageSQLiteMetadataStore is SQLiteMetadataStore


def test_metadata_record_payload_is_deeply_immutable() -> None:
    """Metadata payloads should freeze nested mappings and sequences."""
    record = MetadataRecord.execution_run(
        uuid4(),
        payload={
            "nested": {"count": 1},
            "items": ["a", {"b": 2}],
        },
    )

    assert record.namespace == MetadataNamespaces.EXECUTION_RUNS
    assert record.payload["nested"]["count"] == 1
    assert record.payload["items"][0] == "a"

    with pytest.raises(TypeError):
        record.payload["nested"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        record.payload["nested"]["count"] = 2  # type: ignore[index]
    with pytest.raises(TypeError):
        record.payload["items"][1]["b"] = 3  # type: ignore[index]


def test_sqlite_metadata_store_round_trip_preserves_common_types(
    tmp_path: Path,
) -> None:
    """SQLite metadata storage should round-trip the common structured types used by core."""
    store = SQLiteMetadataStore(tmp_path / "metadata.sqlite3")
    record = MetadataRecord.policy_snapshot(
        uuid4(),
        payload={
            "seen_at": datetime.now(timezone.utc),
            "resource_id": uuid4(),
            "path": Path("runs/0001.json"),
            "tags": ["alpha", "beta"],
        },
    )

    store.put(record)
    loaded = store.get(record.namespace, record.key)

    assert loaded == record
    assert isinstance(loaded.payload["seen_at"], datetime)
    assert isinstance(
        loaded.payload["resource_id"], type(record.payload["resource_id"])
    )
    assert isinstance(loaded.payload["path"], Path)
    assert store.list(namespace=record.namespace) == [record]
    store.close()


def test_in_memory_metadata_store_sorts_records_deterministically() -> None:
    """The in-memory store should preserve deterministic iteration order."""
    store = InMemoryMetadataStore()
    first = MetadataRecord.scheduler("schedule-b", payload={"priority": 2})
    second = MetadataRecord.scheduler("schedule-a", payload={"priority": 1})
    store.put(first)
    store.put(second)

    assert store.list(MetadataNamespaces.SCHEDULER_STATE) == [second, first]


class MetadataMode(Enum):
    FAST = "fast"
    SAFE = "safe"


def test_metadata_enum_round_trip_and_nested_values() -> None:
    """Enum metadata should round-trip through the public codec."""
    payload = {
        "mode": MetadataMode.SAFE,
        "nested": [MetadataMode.FAST, {"mode": MetadataMode.SAFE}],
    }

    encoded = encode_metadata_value(payload)
    decoded = decode_metadata_value(encoded)

    assert decoded == payload
    assert decoded["mode"] is MetadataMode.SAFE
    assert decoded["nested"][0] is MetadataMode.FAST


def test_metadata_enum_registration_rehydrates_after_module_lookup() -> None:
    """Explicit enum registration provides safe cross-process rehydration."""
    register_metadata_enum(MetadataMode)
    encoded = encode_metadata_value(MetadataMode.FAST)

    assert decode_metadata_value(encoded) is MetadataMode.FAST


def test_metadata_enum_decode_does_not_import_untrusted_modules() -> None:
    """Persisted enum references must not trigger arbitrary module imports."""
    import sys

    module_name = "mirror_untrusted_metadata_probe"
    sys.modules.pop(module_name, None)
    encoded = {
        "__mirror_metadata_type__": "enum",
        "enum": f"{module_name}:Exploit",
        "value": "boom",
    }

    assert decode_metadata_value(encoded) == "boom"
    assert module_name not in sys.modules
