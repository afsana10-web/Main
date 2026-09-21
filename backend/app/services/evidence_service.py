"""
Links findings to the specific OCR-derived bounding box evidence that
justified them. If no real bounding box is available, evidence is marked
NOT_AVAILABLE - never fabricated.
"""
from sqlalchemy.orm import Session
from app.models.compliance import Evidence, EvidenceStatus, Finding
from app.models.declaration import Declaration


def build_evidence_for_finding(
    db: Session,
    finding: Finding,
    declaration: Declaration | None,
    extracted_text: str | None,
) -> Evidence:
    if declaration and declaration.bbox_x is not None:
        evidence = Evidence(
            finding_id=finding.id,
            source_image_id=declaration.source_image_id,
            extracted_text=extracted_text,
            status=EvidenceStatus.AVAILABLE,
            bbox_x=declaration.bbox_x,
            bbox_y=declaration.bbox_y,
            bbox_width=declaration.bbox_width,
            bbox_height=declaration.bbox_height,
        )
    else:
        evidence = Evidence(
            finding_id=finding.id,
            source_image_id=declaration.source_image_id if declaration else None,
            extracted_text=extracted_text,
            status=EvidenceStatus.NOT_AVAILABLE,
        )
    db.add(evidence)
    return evidence
