from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.inspection import Inspection
from app.models.compliance import ComplianceCheck, Finding
from app.models.report import Report
from app.services.report_service import generate_inspection_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/{inspection_id}/generate")
def generate_report(
    inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    inspection = (
        db.query(Inspection)
        .options(
            joinedload(Inspection.images),
            joinedload(Inspection.declarations),
            joinedload(Inspection.checks),
            joinedload(Inspection.findings).joinedload(Finding.evidence),
            joinedload(Inspection.findings).joinedload(Finding.verification),
            joinedload(Inspection.officer),
        )
        .filter(Inspection.id == inspection_id)
        .first()
    )
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")

    file_path = generate_inspection_report(inspection, settings.REPORT_DIR)
    report = Report(
        inspection_id=inspection.id,
        file_path=file_path,
        rule_version=inspection.ruleset_version or settings.CURRENT_RULESET_VERSION,
        generated_by=current_user.id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "file_path": file_path}


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return FileResponse(report.file_path, media_type="application/pdf", filename=f"{report.id}_parakh_report.pdf")
