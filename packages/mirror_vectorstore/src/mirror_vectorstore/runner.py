"""Vector store runner – adapts a resolved provider to the capability contract."""

from __future__ import annotations

from .errors import VectorStoreError
from .models import (
    VectorQueryRequest,
    VectorStoreMode,
    VectorStoreRequest,
    VectorStoreResult,
    VectorUpsertRequest,
)
from .protocol import VectorStore


async def vectorstore_step(
    provider: VectorStore, request: VectorStoreRequest
) -> VectorStoreResult:
    """Adapt a VectorStore provider to the capability runner contract."""

    try:
        if request.mode == VectorStoreMode.UPSERT.value:
            result = await provider.upsert(
                VectorUpsertRequest(
                    namespace=request.namespace, records=request.records
                )
            )
            return VectorStoreResult(
                mode=request.mode, namespace=result.namespace, upserted=result.upserted
            )

        query_result = await provider.query(
            VectorQueryRequest(
                namespace=request.namespace,
                vector=request.vector,
                top_k=request.top_k,
                filters=request.filters,
            )
        )
        return VectorStoreResult(
            mode=request.mode,
            namespace=query_result.namespace,
            matches=query_result.matches,
        )
    except VectorStoreError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise VectorStoreError(
            f"Failed to execute vector store operation '{request.mode}'",
            details={"mode": request.mode, "namespace": request.namespace},
            cause=exc,
        ) from exc
