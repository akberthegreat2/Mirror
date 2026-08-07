"""Deterministic text chunking provider."""

from __future__ import annotations

import re

from mirror_chunk.errors import ChunkError
from mirror_chunk.models import Chunk, ChunkDocument, ChunkRequest, ChunkResult
from mirror_chunk.protocol import Chunker
from mirror_chunk.settings import ChunkSettings
from mirror_core.extensions.models import ProviderManifest

_TOKEN_PATTERN = re.compile(r"\S+")


class TextChunkProvider(Chunker):
    """Split text into stable, overlap-aware chunks."""

    def __init__(self, settings: ChunkSettings | None = None) -> None:
        self._settings = settings or ChunkSettings()

    async def chunk(self, request: ChunkRequest) -> ChunkResult:
        """Chunk each document in the request."""

        chunks: list[Chunk] = []
        for document in request.documents:
            chunks.extend(self._chunk_document(document))
        return ChunkResult(chunks=chunks)

    def _chunk_document(self, document: ChunkDocument) -> list[Chunk]:
        tokens = _TOKEN_PATTERN.findall(document.text)
        if not tokens:
            return []

        step = self._settings.chunk_size - self._settings.chunk_overlap
        if step <= 0:
            raise ChunkError("chunk_size must be greater than chunk_overlap")

        chunks: list[Chunk] = []
        start = 0
        chunk_index = 0
        while start < len(tokens):
            end = min(start + self._settings.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}:{chunk_index}",
                    document_id=document.document_id,
                    chunk_index=chunk_index,
                    text=" ".join(chunk_tokens),
                    start_token=start,
                    end_token=end,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_index,
                        "chunk_size": self._settings.chunk_size,
                        "chunk_overlap": self._settings.chunk_overlap,
                    },
                )
            )
            chunk_index += 1
            if end >= len(tokens):
                break
            start += step
        return chunks


provider = ProviderManifest(
    name="text",
    capability="chunk",
    capability_api="~=1.0",
    factory="mirror_chunk_text.provider:TextChunkProvider",
    settings_model="mirror_chunk.settings:ChunkSettings",
    metadata={"description": "Deterministic text chunking provider."},
)
