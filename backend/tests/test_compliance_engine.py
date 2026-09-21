from app.services.declaration_extractor import ExtractedDeclaration
from app.services.compliance_engine import run_compliance_engine
from app.models.rule import ComplianceRule, RuleStatus
import json


def make_rule(id_, category, method, params=None, reason="Checked: {value}"):
    r = ComplianceRule(
        rule_code=f"T{id_}", rule_name="test rule", category=category,
        validation_method=method, validation_params=json.dumps(params or {}),
        reason_template=reason, version="TEST-1", status=RuleStatus.ACTIVE,
    )
    r.id = id_
    return r


def test_required_present_pass():
    rule = make_rule(1, "MRP", "REQUIRED_PRESENT")
    decl = ExtractedDeclaration(field="MRP", detected_value="45.00", normalized_value="45.00",
                                 confidence=0.9, ocr_confidence=95.0, bbox=(1, 1, 1, 1))
    results = run_compliance_engine([rule], [decl], "Food")
    assert results[0].status == "PASS"


def test_required_present_missing_flags_non_compliance():
    rule = make_rule(1, "MRP", "REQUIRED_PRESENT")
    decl = ExtractedDeclaration(field="MRP", detected_value=None, normalized_value=None,
                                 confidence=None, ocr_confidence=None, bbox=None, needs_verification=True)
    results = run_compliance_engine([rule], [decl], "Food")
    assert results[0].status == "POTENTIAL_NON_COMPLIANCE"


def test_low_confidence_never_auto_fails():
    """Critical safety property: low OCR confidence must produce
    NEEDS_VERIFICATION, never POTENTIAL_NON_COMPLIANCE, per project spec."""
    rule = make_rule(1, "MRP", "REQUIRED_PRESENT")
    decl = ExtractedDeclaration(field="MRP", detected_value="45.00", normalized_value="45.00",
                                 confidence=0.5, ocr_confidence=20.0, bbox=(1, 1, 1, 1))
    results = run_compliance_engine([rule], [decl], "Food")
    assert results[0].status == "NEEDS_VERIFICATION"


def test_numeric_range_out_of_bounds():
    rule = make_rule(1, "MRP", "NUMERIC_RANGE", params={"min": 1, "max": 1000})
    decl = ExtractedDeclaration(field="MRP", detected_value="0.01", normalized_value="0.01",
                                 confidence=0.9, ocr_confidence=95.0, bbox=(1, 1, 1, 1))
    results = run_compliance_engine([rule], [decl], "Food")
    assert results[0].status == "POTENTIAL_NON_COMPLIANCE"


def test_applicability_gate_restricts_category():
    rule = make_rule(1, "BEST_BEFORE_USE_BY", "REQUIRED_PRESENT", params={"applicable_categories": ["food"]})
    decl = ExtractedDeclaration(field="BEST_BEFORE_USE_BY", detected_value=None, normalized_value=None,
                                 confidence=None, ocr_confidence=None, bbox=None, needs_verification=True)
    results = run_compliance_engine([rule], [decl], "Hardware")
    assert results[0].status == "NOT_APPLICABLE"
