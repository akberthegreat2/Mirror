"""Typed models for the Compliance capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class ComplianceDocument:
    """A document to validate against compliance rules."""

    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ComplianceRule(BaseModel):
    """A deterministic policy rule."""

    rule_id: str = Field(min_length=1)
    severity: Literal["info", "warn", "error"] = "error"
    forbidden_terms: tuple[str, ...] = Field(default_factory=tuple)
    required_metadata_keys: tuple[str, ...] = Field(default_factory=tuple)
    max_characters: int | None = Field(default=None, ge=1)
    min_unique_words: int | None = Field(default=None, ge=1)
    case_sensitive: bool = False


@dataclass(slots=True, frozen=True)
class ComplianceFinding:
    """A single compliance finding for one rule."""

    rule_id: str
    passed: bool
    severity: Literal["info", "warn", "error"]
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class ComplianceAssessment(BaseModel):
    """A compliance assessment for a single document."""

    document_id: str
    compliant: bool
    findings: list[ComplianceFinding] = Field(default_factory=list)


class ComplianceRequest(BaseModel):
    """Input for a compliance run."""

    documents: list[ComplianceDocument] = Field(default_factory=list)
    rules: list[ComplianceRule] = Field(default_factory=list)


class ComplianceResult(BaseModel):
    """Output of a compliance run."""

    assessments: list[ComplianceAssessment] = Field(default_factory=list)
    compliant: bool = True
    passed_count: int = 0
    failed_count: int = 0
