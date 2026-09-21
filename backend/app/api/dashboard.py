from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.inspection import Inspection, OverallStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.query(func.count(Inspection.id)).scalar() or 0
    compliant = db.query(func.count(Inspection.id)).filter(Inspection.status == OverallStatus.COMPLIANT).scalar() or 0
    issues = db.query(func.count(Inspection.id)).filter(
        Inspection.status == OverallStatus.POTENTIAL_NON_COMPLIANCE
    ).scalar() or 0
    pending_verification = db.query(func.count(Inspection.id)).filter(
        Inspection.status == OverallStatus.NEEDS_OFFICER_VERIFICATION
    ).scalar() or 0

    by_status = dict(
        db.query(Inspection.status, func.count(Inspection.id)).group_by(Inspection.status).all()
    )
    by_status = {k.value: v for k, v in by_status.items()}

    by_category = dict(
        db.query(Inspection.category, func.count(Inspection.id))
        .filter(Inspection.status == OverallStatus.POTENTIAL_NON_COMPLIANCE)
        .group_by(Inspection.category)
        .all()
    )

    recent = (
        db.query(Inspection)
        .order_by(Inspection.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_inspections": total,
        "compliant": compliant,
        "potential_issues": issues,
        "pending_verification": pending_verification,
        "inspections_by_status": by_status,
        "issues_by_category": by_category,
        "recent_inspections": [
            {
                "id": i.id,
                "inspection_code": i.inspection_code,
                "product_name": i.product_name,
                "category": i.category,
                "status": i.status.value,
                "inspection_date": i.inspection_date.isoformat(),
            }
            for i in recent
        ],
    }
