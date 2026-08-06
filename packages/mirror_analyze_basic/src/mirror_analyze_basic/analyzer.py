"""Lightweight text analysis helpers."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from mirror_analyze.models import AnalyzerResult


@dataclass(slots=True)
class Analyzer:
    def analyze(self, text: str) -> AnalyzerResult:
        tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9']+", text)]
        counts = Counter(tokens)
        keywords = tuple(token for token, _ in counts.most_common(12))
        entities: tuple[tuple[str, str], ...] = tuple()
        summary = " ".join(text.split())[:240]
        return AnalyzerResult(
            language="en",
            keywords=keywords,
            entities=entities,
            summary=summary,
            token_count=len(tokens),
        )
