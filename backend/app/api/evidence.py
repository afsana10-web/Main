from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.inspection import Inspection
from app.schemas.results import EvidenceOut

router = APIRouter(prefix="/api/inspections", tags=["evidence"])


@router.get("/{inspection_id}/evidence", response_model=list[EvidenceOut])
def get_inspection_evidence(
    inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")
    return [f.evidence for f in inspection.findings if f.evidence is not None]
