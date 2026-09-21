"""
Orchestrates the full PARAKH pipeline for one inspection:
Images -> Preprocessing -> OCR -> Declaration Extraction -> Compliance Engine
-> Findings + Evidence -> Overall Status
"""
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inspection import Inspection, OverallStatus
from app.models.ocr import OCRResult, OCRWord
from app.models.declaration import Declaration, DeclarationField
from app.models.rule import ComplianceRule, RuleStatus
from app.models.compliance import ComplianceCheck, CheckStatus, Finding
from app.services import image_processing, ocr_service, declaration_extractor, compliance_engine, evidence_service


def generate_inspection_code() -> str:
    return f"PKH-{uuid.uuid4().hex[:8].upper()}"


def run_full_analysis(db: Session, inspection: Inspection) -> Inspection:
    """Runs preprocessing + OCR on every image, merges declarations across
    images (keeping the highest-confidence detection per field), runs the
    compliance engine, and creates findings + evidence. Mutates and commits
    the inspection."""

    all_declarations: dict[str, tuple] = {}  # field -> (ExtractedDeclaration, image_id)

    for img in inspection.images:
        # 1. Preprocess (never touches the original)
        try:
            preprocessed_path = image_processing.preprocess_image(
                img.original_path, output_dir=f"{settings.UPLOAD_DIR}/preprocessed"
            )
            img.preprocessed_path = preprocessed_path
        except Exception:
            preprocessed_path = img.original_path  # fall back to original for OCR

        w, h = image_processing.get_image_dimensions(img.original_path)
        img.width, img.height = w, h
        quality, reason = image_processing.assess_quality(img.original_path)
        img.quality = quality
        img.quality_reason = reason

        # 2. OCR (real Tesseract call on the preprocessed image)
        ocr_run = ocr_service.run_ocr(img.original_path)

        print("\n========== PARAKH OCR TEXT ==========")
        print(ocr_run.full_text)
        print("========== END OCR TEXT ==========\n")

        ocr_row = OCRResult(
            image_id=img.id,
            full_text=ocr_run.full_text,
            mean_confidence=ocr_run.mean_confidence,
            engine="tesseract",
        )
        db.add(ocr_row)
        db.flush()
        for w_res in ocr_run.words:
            db.add(OCRWord(
                ocr_result_id=ocr_row.id, text=w_res.text, confidence=w_res.confidence,
                x=w_res.x, y=w_res.y, width=w_res.width, height=w_res.height,
                line_num=w_res.line_num, word_num=w_res.word_num,
            ))

        # 3. Declaration extraction for this image
        extracted = declaration_extractor.extract_declarations(ocr_run.full_text, ocr_run.words)
        for decl in extracted:
            if decl.detected_value is None:
                continue
            existing = all_declarations.get(decl.field)
            # keep the higher-confidence detection across multiple images
            if existing is None or (decl.ocr_confidence or 0) > (existing[0].ocr_confidence or 0):
                all_declarations[decl.field] = (decl, img.id)

    # Ensure every known field has an entry (even if never detected on any image)
    for field_enum in DeclarationField:
        if field_enum.value not in all_declarations:
            all_declarations[field_enum.value] = (
                declaration_extractor.ExtractedDeclaration(
                    field=field_enum.value, detected_value=None, normalized_value=None,
                    confidence=None, ocr_confidence=None, bbox=None, needs_verification=True,
                ),
                None,
            )

    declaration_rows: dict[str, Declaration] = {}
    for field_name, (decl, image_id) in all_declarations.items():
        bbox = decl.bbox
        row = Declaration(
            inspection_id=inspection.id,
            field=DeclarationField(field_name),
            detected_value=decl.detected_value,
            normalized_value=decl.normalized_value,
            source_image_id=image_id,
            ocr_confidence=decl.ocr_confidence,
            bbox_x=bbox[0] if bbox else None,
            bbox_y=bbox[1] if bbox else None,
            bbox_width=bbox[2] if bbox else None,
            bbox_height=bbox[3] if bbox else None,
            extraction_confidence=decl.confidence,
            needs_verification=decl.needs_verification,
        )
        db.add(row)
        declaration_rows[field_name] = row
    db.flush()

    # 4. Compliance engine
    rules = db.query(ComplianceRule).filter(ComplianceRule.status == RuleStatus.ACTIVE).all()
    extracted_list = [d for d, _ in all_declarations.values()]
    check_results = compliance_engine.run_compliance_engine(rules, extracted_list, inspection.category)

    worst_status = OverallStatus.COMPLIANT
    for cr in check_results:
        check_row = ComplianceCheck(
            inspection_id=inspection.id,
            rule_id=cr.rule_id,
            rule_version=cr.rule_version,
            declaration_id=declaration_rows.get(cr.declaration_field).id if cr.declaration_field in declaration_rows else None,
            declaration_field=cr.declaration_field,
            detected_value=cr.detected_value,
            status=CheckStatus(cr.status),
            confidence=cr.confidence,
            reason=cr.reason,
        )
        db.add(check_row)
        db.flush()

        if cr.status in ("POTENTIAL_NON_COMPLIANCE", "NEEDS_VERIFICATION"):
            finding = Finding(
                inspection_id=inspection.id,
                check_id=check_row.id,
                title=f"{cr.declaration_field.replace('_', ' ').title()} - {cr.status.replace('_', ' ').title()}",
                expected="Declared per Legal Metrology (Packaged Commodities) Rules, 2011",
                detected=cr.detected_value or "Not detected",
                severity="HIGH" if cr.status == "POTENTIAL_NON_COMPLIANCE" else "LOW",
            )
            db.add(finding)
            db.flush()
            decl_row = declaration_rows.get(cr.declaration_field)
            evidence_service.build_evidence_for_finding(db, finding, decl_row, decl_row.detected_value if decl_row else None)

        if cr.status == "POTENTIAL_NON_COMPLIANCE":
            worst_status = OverallStatus.POTENTIAL_NON_COMPLIANCE
        elif cr.status == "NEEDS_VERIFICATION" and worst_status != OverallStatus.POTENTIAL_NON_COMPLIANCE:
            worst_status = OverallStatus.NEEDS_OFFICER_VERIFICATION

    inspection.status = worst_status
    inspection.ruleset_version = settings.CURRENT_RULESET_VERSION
    from datetime import datetime
    inspection.analyzed_at = datetime.utcnow()

    db.commit()
    db.refresh(inspection)
    return inspection
