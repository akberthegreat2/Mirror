"""Concurrent-safe WARC archive provider implementation."""

from __future__ import annotations

import asyncio
import hashlib
import io
from datetime import datetime, timezone
from io import BufferedWriter
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

from mirror_archive.exceptions import ArchiveError
from mirror_archive.models import ArchiveRequest, ArchiveResult
from mirror_archive.protocol import Archive
from mirror_core.lifecycle import AsyncLifecycle

from mirror_archive_warc.settings import WARCSettings


class WARCProvider(AsyncLifecycle, Archive):
    """Write typed archive payloads to rotating WARC resource records.

    The provider owns one active WARC segment at a time. Calls are serialized
    with an async lock because ``warcio`` writers and their underlying streams
    are not safe for concurrent writes. Blocking file and WARC work is moved to
    a worker thread so archive operations do not block the event loop.

    Lifecycle is explicit: callers must invoke :meth:`setup` before
    :meth:`archive`, normally through ``mirror_core.Application``.
    """

    _metadata_prefix: ClassVar[str] = "Mirror-Metadata-"

    def __init__(self, settings: WARCSettings | None = None) -> None:
        self._settings = settings or WARCSettings()
        self._output_dir = self._settings.output_dir
        self._writer: Any = None
        self._current_file: Path | None = None
        self._file: BufferedWriter | None = None
        self._lock = asyncio.Lock()
        self._records = 0
        self._payload_bytes = 0

    @staticmethod
    def _load_writer_class() -> type[Any]:
        """Load the optional ``warcio`` writer lazily.

        Returns:
            The ``warcio.warcwriter.WARCWriter`` class.

        Raises:
            ArchiveError: If the optional dependency is unavailable.
        """

        try:
            from warcio.warcwriter import WARCWriter
        except ImportError as exc:
            raise ArchiveError("WARC provider requires the 'warcio' dependency") from exc
        return WARCWriter

    async def setup(self) -> None:
        """Open an initial WARC segment.

        Repeated calls are idempotent.
        """

        async with self._lock:
            if self._writer is not None:
                return
            await asyncio.to_thread(self._open_segment)

    async def teardown(self) -> None:
        """Flush and close the active segment.

        Repeated calls are idempotent.
        """

        async with self._lock:
            await asyncio.to_thread(self._close_segment)

    async def archive(self, request: ArchiveRequest) -> ArchiveResult:
        """Write one archive request as a WARC ``resource`` record.

        Args:
            request: Typed payload and metadata to archive.

        Returns:
            Metadata identifying the segment and payload checksum.

        Raises:
            ArchiveError: If lifecycle setup was not completed or writing
                fails.
        """

        async with self._lock:
            if self._writer is None or self._current_file is None:
                raise ArchiveError("WARC provider is not initialized; call setup() first")

            try:
                incoming_bytes = len(request.payload.content)
            except (AttributeError, TypeError) as exc:
                raise ArchiveError("Archive request contains an invalid payload", cause=exc) from exc

            if self._should_rotate(incoming_bytes):
                await asyncio.to_thread(self._rotate_segment)

            return await asyncio.to_thread(self._write_request, request)

    def _open_segment(self) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        writer_class = self._load_writer_class()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        suffix = ".warc.gz" if self._settings.compress else ".warc"
        path = self._output_dir / f"mirror-{timestamp}-{uuid4().hex[:8]}{suffix}"

        file_obj: BufferedWriter | None = None
        try:
            file_obj = path.open("wb")
            writer = writer_class(file_obj, gzip=self._settings.compress)
        except Exception as exc:
            if file_obj is not None:
                file_obj.close()
            raise ArchiveError(f"Failed to open WARC segment {path}: {exc}", cause=exc) from exc

        self._current_file = path
        self._file = file_obj
        self._writer = writer
        self._records = 0
        self._payload_bytes = 0

    def _close_segment(self) -> None:
        file_obj = self._file
        self._writer = None
        self._file = None
        self._current_file = None
        self._records = 0
        self._payload_bytes = 0

        if file_obj is not None:
            try:
                file_obj.flush()
            finally:
                file_obj.close()

    def _rotate_segment(self) -> None:
        self._close_segment()
        self._open_segment()

    def _should_rotate(self, incoming_bytes: int) -> bool:
        if self._records == 0:
            return False
        return (
            self._records >= self._settings.max_records
            or self._payload_bytes + incoming_bytes > self._settings.max_file_bytes
        )

    def _write_request(self, request: ArchiveRequest) -> ArchiveResult:
        writer = self._writer
        current_file = self._current_file
        if writer is None or current_file is None:
            raise ArchiveError("WARC provider lost its active segment")

        try:
            content = request.payload.content
            digest = hashlib.sha256(content).hexdigest()
            warc_headers = self._build_warc_headers(request, digest)
            record = writer.create_warc_record(
                uri=request.payload.target_uri,
                record_type="resource",
                payload=io.BytesIO(content),
                length=len(content),
                warc_content_type=request.payload.media_type,
                warc_headers_dict=warc_headers,
            )
            writer.write_record(record)
        except ArchiveError:
            raise
        except Exception as exc:
            raise ArchiveError(
                f"Failed to archive {request.resource_id}: {exc}",
                details={"resource_id": str(request.resource_id)},
                cause=exc,
            ) from exc

        self._records += 1
        self._payload_bytes += len(content)
        return ArchiveResult(
            archive_id=uuid4(),
            path=str(current_file),
            size=len(content),
            checksum=f"sha256:{digest}",
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def _build_warc_headers(
        self,
        request: ArchiveRequest,
        digest: str,
    ) -> dict[str, str]:
        """Build valid additional WARC headers.

        ``warcio`` creates required WARC headers such as ``WARC-Type``,
        ``WARC-Date``, ``WARC-Record-ID`` and ``WARC-Target-URI``. This method
        supplies only optional headers and sanitized Mirror metadata.
        """

        headers: dict[str, str] = {
            "WARC-Payload-Digest": f"sha256:{digest}",
            "WARC-Refers-To": f"<urn:uuid:{request.resource_id}>",
        }
        combined_metadata: dict[str, Any] = {
            **request.metadata,
            **{f"payload-header-{key}": value for key, value in request.payload.headers.items()},
        }
        for key, value in combined_metadata.items():
            safe_key = self._sanitize_header_name(str(key))
            if not safe_key:
                continue
            headers[f"{self._metadata_prefix}{safe_key}"] = self._sanitize_header_value(value)
        return headers

    @staticmethod
    def _sanitize_header_name(value: str) -> str:
        return "".join(ch for ch in value if ch.isalnum() or ch in "-_")[:64]

    @staticmethod
    def _sanitize_header_value(value: Any) -> str:
        return str(value).replace("\r", " ").replace("\n", " ")[:4096]
