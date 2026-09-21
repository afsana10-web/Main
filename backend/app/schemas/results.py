from datetime import datetime
from pydantic import BaseModel
from app.models.declaration import DeclarationField
from app.models.compliance import CheckStatus, EvidenceStatus


class DeclarationOut(BaseModel):
    id: int
    field: DeclarationField
    detected_value: str | None
    normalized_value: str | None
    source_image_id: int | None
    ocr_confidence: float | None
    bbox_x: int | None
    bbox_y: int | None
    bbox_width: int | None
    bbox_height: int | None
    needs_verification: bool

    class Config:
        from_attributes = True


class EvidenceOut(BaseModel):
    id: int
    source_image_id: int | None
    extracted_text: str | None
    status: EvidenceStatus
    bbox_x: int | None
    bbox_y: int | None
    bbox_width: int | None
    bbox_height: int | None

    class Config:
        from_attributes = True


class VerificationOut(BaseModel):
    id: int
    officer_id: int
    decision: str
    corrected_value: str | None
    remarks: str | None
    verification_date: datetime

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: int
    title: str
    expected: str | None
    detected: str | None
    severity: str
    check_id: int
    evidence: EvidenceOut | None = None
    verification: VerificationOut | None = None

    class Config:
        from_attributes = True


class ComplianceCheckOut(BaseModel):
    id: int
    rule_id: int
    rule_version: str
    declaration_field: str
    detected_value: str | None
    status: CheckStatus
    confidence: float | None
    reason: str
    finding: FindingOut | None = None

    class Config:
        from_attributes = True


class InspectionResultsOut(BaseModel):
    inspection_id: int
    overall_status: str
    ruleset_version: str | None
    declarations: list[DeclarationOut]
    checks: list[ComplianceCheckOut]


class VerifyFindingRequest(BaseModel):
    decision: str  # CONFIRMED / REJECTED / MODIFIED
    corrected_value: str | None = None
    remarks: str | None = None
