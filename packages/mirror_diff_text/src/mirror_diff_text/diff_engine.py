"""Text diff helpers."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff

from mirror_diff.models import DiffSummary


@dataclass(slots=True)
class DiffEngine:
    def compare(self, before: str, after: str) -> DiffSummary:
        before_lines = before.splitlines()
        after_lines = after.splitlines()
        matcher = SequenceMatcher(a=before_lines, b=after_lines)
        diff_text = "\n".join(unified_diff(before_lines, after_lines, lineterm=""))
        added = tuple(line[1:] for line in after_lines if line not in before_lines)
        removed = tuple(line[1:] for line in before_lines if line not in after_lines)
        return DiffSummary(
            ratio=matcher.ratio(),
            unified_diff=diff_text,
            added_lines=added,
            removed_lines=removed,
            changed=before != after,
        )
