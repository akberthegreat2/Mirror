"""Deterministic compliance provider."""

from __future__ import annotations

import re

from mirror_compliance.models import (
    ComplianceAssessment,
    ComplianceDocument,
    ComplianceFinding,
    ComplianceRequest,
    ComplianceResult,
    ComplianceRule,
)
from mirror_compliance.protocol import ComplianceChecker
from mirror_compliance.settings import ComplianceSettings
from mirror_core.extensions.models import ProviderManifest

TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


class RulesComplianceProvider(ComplianceChecker):
    """Evaluate documents against explicit text and metadata rules."""

    def __init__(self, settings: ComplianceSettings | None = None) -> None:
        self._settings = settings or ComplianceSettings()

    async def check(self, request: ComplianceRequest) -> ComplianceResult:
        """Evaluate a batch of documents against policy rules."""

        rules = self._merge_rules(request.rules)
        assessments = [self._check_document(document, rules) for document in request.documents]
        compliant = all(assessment.compliant for assessment in assessments)
        passed_count = sum(1 for assessment in assessments if assessment.compliant)
        failed_count = len(assessments) - passed_count
        return ComplianceResult(
            assessments=assessments,
            compliant=compliant,
            passed_count=passed_count,
            failed_count=failed_count,
        )

    def _merge_rules(self, rules: list[ComplianceRule]) -> list[ComplianceRule]:
        """Combine request rules with the default settings-backed rule set."""

        merged: list[ComplianceRule] = list(rules)
        defaults = ComplianceRule(
            rule_id="default-policy",
            severity="error",
            forbidden_terms=self._settings.forbidden_terms,
            required_metadata_keys=self._settings.required_metadata_keys,
            max_characters=self._settings.max_characters,
            min_unique_words=self._settings.min_unique_words,
            case_sensitive=self._settings.case_sensitive,
        )
        if any(
            (
                defaults.forbidden_terms,
                defaults.required_metadata_keys,
                defaults.max_characters is not None,
                defaults.min_unique_words is not None,
            )
        ):
            merged.append(defaults)
        return merged

    def _check_document(self, document: ComplianceDocument, rules: list[ComplianceRule]) -> ComplianceAssessment:
        """Evaluate a single document against every rule."""

        findings = [self._evaluate_rule(document, rule) for rule in rules]
        compliant = all(finding.passed for finding in findings) if findings else True
        return ComplianceAssessment(
            document_id=document.document_id,
            compliant=compliant,
            findings=findings,
        )

    def _evaluate_rule(self, document: ComplianceDocument, rule: ComplianceRule) -> ComplianceFinding:
        """Evaluate one document against one rule."""

        normalized_text = document.text if rule.case_sensitive else document.text.casefold()
        normalized_terms = tuple(term if rule.case_sensitive else term.casefold() for term in rule.forbidden_terms)
        words = TOKEN_RE.findall(normalized_text)
        unique_words = len(set(words))
        metadata_keys = set(document.metadata)

        if rule.max_characters is not None and len(document.text) > rule.max_characters:
            return ComplianceFinding(
                rule_id=rule.rule_id,
                passed=False,
                severity=rule.severity,
                message=f"Document exceeds maximum length of {rule.max_characters} characters.",
                details={
                    "character_count": len(document.text),
                    "maximum": rule.max_characters,
                },
            )
        if rule.min_unique_words is not None and unique_words < rule.min_unique_words:
            return ComplianceFinding(
                rule_id=rule.rule_id,
                passed=False,
                severity=rule.severity,
                message=f"Document has fewer than {rule.min_unique_words} unique words.",
                details={
                    "unique_words": unique_words,
                    "minimum": rule.min_unique_words,
                },
            )
        missing_keys = [key for key in rule.required_metadata_keys if key not in metadata_keys]
        if missing_keys:
            return ComplianceFinding(
                rule_id=rule.rule_id,
                passed=False,
                severity=rule.severity,
                message="Document is missing required metadata keys.",
                details={"missing_keys": missing_keys},
            )
        forbidden_hits = [term for term in normalized_terms if term and term in normalized_text]
        if forbidden_hits:
            return ComplianceFinding(
                rule_id=rule.rule_id,
                passed=False,
                severity=rule.severity,
                message="Document contains forbidden terms.",
                details={"forbidden_terms": forbidden_hits},
            )
        return ComplianceFinding(
            rule_id=rule.rule_id,
            passed=True,
            severity=rule.severity,
            message="Document passed compliance checks.",
            details={"word_count": len(words), "unique_words": unique_words},
        )


def build_provider(settings: ComplianceSettings) -> RulesComplianceProvider:
    """Build a compliance provider from settings."""

    return RulesComplianceProvider(settings=settings)


provider = ProviderManifest(
    name="rules",
    capability="compliance",
    capability_api="~=1.0",
    factory="mirror_compliance_rules.provider:build_provider",
    settings_model="mirror_compliance.settings:ComplianceSettings",
    metadata={"description": "Deterministic policy compliance provider."},
)
