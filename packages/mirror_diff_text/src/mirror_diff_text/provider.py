"""Text diff provider."""

from __future__ import annotations

from mirror_core.registry import ProviderConfig
from mirror_diff.models import DiffRequest, DiffResult
from mirror_diff.protocol import Diff

from .diff_engine import DiffEngine


class TextDiffProvider(Diff):
    async def diff(self, request: DiffRequest) -> DiffResult:
        return DiffResult(summary=DiffEngine().compare(request.before, request.after))


provider = ProviderConfig(
    name="text",
    capability="diff",
    capability_api="~=1.0",
    factory="mirror_diff_text.provider:TextDiffProvider",
    metadata={"description": "Text diff provider."},
)
