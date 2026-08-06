"""Typed analysis-domain models."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class AnalyzerResult:
    language: str
    keywords: tuple[str, ...]
    entities: tuple[tuple[str, str], ...]
    summary: str
    token_count: int


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)


class AnalyzeResult(BaseModel):
    analysis: AnalyzerResult
