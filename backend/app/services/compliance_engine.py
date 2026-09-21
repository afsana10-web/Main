"""
Configurable, rule-driven compliance engine.

Design principle (per project spec): rules are DATA, not code. This module
contains only generic validation *methods*; the actual legal thresholds,
regex patterns, and applicability conditions live in the ComplianceRule
rows (seeded from compliance-rules/rules.json) so rules can be
added/edited/versioned without touching engine code.

Also per spec: low OCR/extraction confidence must never automatically
become POTENTIAL_NON_COMPLIANCE - it becomes NEEDS_VERIFICATION instead.
Poor image quality is handled the same way upstream.
"""
import json
import re
from dataclasses import dataclass
from app.models.rule import ComplianceRule
from app.services.declaration_extractor import ExtractedDeclaration

LOW_CONFIDENCE_THRESHOLD = 60.0


@dataclass
class CheckResult:
    rule_id: int
    rule_version: str
    declaration_field: str
    detected_value: str | None
    status: str  # PASS / POTENTIAL_NON_COMPLIANCE / NEEDS_VERIFICATION / NOT_APPLICABLE
    confidence: float | None
    reason: str


def _params(rule: ComplianceRule) -> dict:
    if not rule.validation_params:
        return {}
    try:
        return json.loads(rule.validation_params)
    except json.JSONDecodeError:
        return {}


def _low_confidence(decl: ExtractedDeclaration) -> bool:
    if decl.needs_verification:
        return True
    if decl.ocr_confidence is not None and decl.ocr_confidence < LOW_CONFIDENCE_THRESHOLD:
        return True
    return False


def _evaluate_required_present(rule: ComplianceRule, decl: ExtractedDeclaration | None) -> CheckResult:
    if decl is None or not decl.detected_value:
        return CheckResult(
            rule.id, rule.version, rule.category, None, "POTENTIAL_NON_COMPLIANCE",
            None, rule.reason_template.format(value="not detected on any package image"),
        )
    if _low_confidence(decl):
        return CheckResult(
            rule.id, rule.version, rule.category, decl.detected_value, "NEEDS_VERIFICATION",
            decl.ocr_confidence,
            "Declaration appears present but OCR/extraction confidence is low or the "
            "match is uncertain - officer verification of the physical package is required.",
        )
    return CheckResult(
        rule.id, rule.version, rule.category, decl.detected_value, "PASS",
        decl.ocr_confidence, rule.reason_template.format(value=decl.detected_value),
    )


def _evaluate_regex_match(rule: ComplianceRule, decl: ExtractedDeclaration | None) -> CheckResult:
    params = _params(rule)
    pattern = params.get("pattern")
    if decl is None or not decl.detected_value:
        return CheckResult(
            rule.id, rule.version, rule.category, None, "POTENTIAL_NON_COMPLIANCE",
            None, rule.reason_template.format(value="not detected"),
        )
    if _low_confidence(decl):
        return CheckResult(
            rule.id, rule.version, rule.category, decl.detected_value, "NEEDS_VERIFICATION",
            decl.ocr_confidence, "Low confidence extraction - requires officer verification.",
        )
    if pattern and not re.search(pattern, decl.detected_value, flags=re.IGNORECASE):
        return CheckResult(
            rule.id, rule.version, rule.category, decl.detected_value, "POTENTIAL_NON_COMPLIANCE",
            decl.ocr_confidence,
            rule.reason_template.format(value=decl.detected_value) + " (format does not match the expected pattern)",
        )
    return CheckResult(
        rule.id, rule.version, rule.category, decl.detected_value, "PASS",
        decl.ocr_confidence, rule.reason_template.format(value=decl.detected_value),
    )


def _evaluate_numeric_range(rule: ComplianceRule, decl: ExtractedDeclaration | None) -> CheckResult:
    params = _params(rule)
    min_v, max_v = params.get("min"), params.get("max")
    if decl is None or not decl.detected_value:
        return CheckResult(
            rule.id, rule.version, rule.category, None, "NEEDS_VERIFICATION",
            None, "Value not detected - cannot assess numeric range automatically.",
        )
    if _low_confidence(decl):
        return CheckResult(
            rule.id, rule.version, rule.category, decl.detected_value, "NEEDS_VERIFICATION",
            decl.ocr_confidence, "Low confidence extraction - requires officer verification.",
        )
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", decl.detected_value)
    if not match:
        return CheckResult(
            rule.id, rule.version, rule.category, decl.detected_value, "NEEDS_VERIFICATION",
            decl.ocr_confidence, "Could not parse a numeric value for range validation.",
        )
    value = float(match.group(0))
    if (min_v is not None and value < min_v) or (max_v is not None and value > max_v):
        return CheckResult(
            rule.id, rule.version, rule.category, decl.detected_value, "POTENTIAL_NON_COMPLIANCE",
            decl.ocr_confidence,
            rule.reason_template.format(value=decl.detected_value) + f" (expected range {min_v}-{max_v})",
        )
    return CheckResult(
        rule.id, rule.version, rule.category, decl.detected_value, "PASS",
        decl.ocr_confidence, rule.reason_template.format(value=decl.detected_value),
    )


def _evaluate_not_applicable(rule: ComplianceRule, decl: ExtractedDeclaration | None) -> CheckResult:
    return CheckResult(
        rule.id, rule.version, rule.category, decl.detected_value if decl else None,
        "NOT_APPLICABLE", None, rule.reason_template,
    )


VALIDATORS = {
    "REQUIRED_PRESENT": _evaluate_required_present,
    "REGEX_MATCH": _evaluate_regex_match,
    "NUMERIC_RANGE": _evaluate_numeric_range,
    "NOT_APPLICABLE": _evaluate_not_applicable,
}


def is_applicable(rule: ComplianceRule, category: str) -> bool:
    """Very simple applicability gate: a rule with an `applicable_categories`
    param restricts itself to those product categories (case-insensitive
    substring match); otherwise it applies to everything."""
    params = _params(rule)
    applicable_categories = params.get("applicable_categories")
    if not applicable_categories:
        return True
    return any(c.lower() in category.lower() for c in applicable_categories)


def run_compliance_engine(
    rules: list[ComplianceRule],
    declarations: list[ExtractedDeclaration],
    product_category: str,
) -> list[CheckResult]:
    """Evaluates every active rule against the extracted declarations for
    this inspection. Returns one CheckResult per rule."""
    decl_by_field = {d.field: d for d in declarations}
    results: list[CheckResult] = []

    for rule in rules:
        if rule.status.value != "ACTIVE":
            continue
        if not is_applicable(rule, product_category):
            results.append(
                CheckResult(
                    rule.id, rule.version, rule.category, None, "NOT_APPLICABLE",
                    None, "Rule does not apply to this product category.",
                )
            )
            continue

        decl = decl_by_field.get(rule.category)
        validator = VALIDATORS.get(rule.validation_method, _evaluate_required_present)
        results.append(validator(rule, decl))

    return results
