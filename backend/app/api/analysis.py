from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.inspection import Inspection
from app.models.compliance import ComplianceCheck, Finding
from app.schemas.results import InspectionResultsOut, FindingOut

router = APIRouter(prefix="/api/inspections", tags=["analysis"])


@router.get("/{inspection_id}/results", response_model=InspectionResultsOut)
def get_results(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inspection = (
        db.query(Inspection)
        .options(
            joinedload(Inspection.declarations),
            joinedload(Inspection.checks).joinedload(ComplianceCheck.finding).joinedload(Finding.evidence),
            joinedload(Inspection.checks).joinedload(ComplianceCheck.finding).joinedload(Finding.verification),
        )
        .filter(Inspection.id == inspection_id)
        .first()
    )
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")

    return InspectionResultsOut(
        inspection_id=inspection.id,
        overall_status=inspection.status.value,
        ruleset_version=inspection.ruleset_version,
        declarations=inspection.declarations,
        checks=inspection.checks,
    )


@router.get("/{inspection_id}/findings", response_model=list[FindingOut])
def get_findings(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")
    return inspection.findings
