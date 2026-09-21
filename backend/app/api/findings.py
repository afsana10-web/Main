from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.compliance import Finding
from app.models.verification import VerificationRecord, OfficerDecision
from app.schemas.results import FindingOut, VerifyFindingRequest

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")
    return finding


@router.post("/{finding_id}/verify", response_model=FindingOut)
def verify_finding(
    finding_id: int,
    payload: VerifyFindingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")

    try:
        decision = OfficerDecision(payload.decision.upper())
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "decision must be CONFIRMED, REJECTED, or MODIFIED")

    if decision == OfficerDecision.MODIFIED and not payload.corrected_value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "corrected_value is required when decision is MODIFIED")

    existing = db.query(VerificationRecord).filter(VerificationRecord.finding_id == finding.id).first()
    if existing:
        # An officer can update their own verification record, but the
        # original automated finding/check is NEVER modified here.
        existing.decision = decision
        existing.corrected_value = payload.corrected_value
        existing.remarks = payload.remarks
        existing.officer_id = current_user.id
        existing.verification_date = datetime.utcnow()
    else:
        record = VerificationRecord(
            finding_id=finding.id,
            officer_id=current_user.id,
            decision=decision,
            corrected_value=payload.corrected_value,
            remarks=payload.remarks,
        )
        db.add(record)

    db.commit()

    # Recompute inspection-level verified timestamp
    inspection = finding.inspection
    inspection.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(finding)
    return finding


@router.put("/{finding_id}", response_model=FindingOut)
def update_finding_metadata(
    finding_id: int,
    payload: VerifyFindingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias to verify - kept for REST-completeness per the documented API surface."""
    return verify_finding(finding_id, payload, db, current_user)
