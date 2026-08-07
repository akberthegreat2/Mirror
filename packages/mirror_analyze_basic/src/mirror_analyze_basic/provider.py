"""Basic Analyze provider."""

from __future__ import annotations

from mirror_analyze.models import AnalyzeRequest, AnalyzeResult
from mirror_analyze.protocol import Analyze
from mirror_core.extensions.models import ProviderManifest

from .analyzer import Analyzer


class BasicAnalyzeProvider(Analyze):
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResult:
        return AnalyzeResult(analysis=Analyzer().analyze(request.text))


provider = ProviderManifest(
    name="basic",
    capability="analyze",
    capability_api="~=1.0",
    factory="mirror_analyze_basic.provider:BasicAnalyzeProvider",
    metadata={"description": "Basic content-analysis provider."},
)
