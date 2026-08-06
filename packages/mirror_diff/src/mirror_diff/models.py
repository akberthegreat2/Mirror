"""Typed diff-domain models."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class DiffSummary:
    ratio: float
    unified_diff: str
    added_lines: tuple[str, ...]
    removed_lines: tuple[str, ...]
    changed: bool


class DiffRequest(BaseModel):
    before: str = Field(min_length=1)
    after: str = Field(min_length=1)


class DiffResult(BaseModel):
    summary: DiffSummary
