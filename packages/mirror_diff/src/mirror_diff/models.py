"""Typed diff-domain models."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class DiffSummary:
    """Summary of a document diff."""

    ratio: float
    unified_diff: str
    added_lines: tuple[str, ...]
    removed_lines: tuple[str, ...]
    changed: bool


class DiffRequest(BaseModel):
    """Input for a diff operation."""

    before: str = Field(min_length=1)
    after: str = Field(min_length=1)


class DiffResult(BaseModel):
    """Output of a diff operation."""

    summary: DiffSummary
