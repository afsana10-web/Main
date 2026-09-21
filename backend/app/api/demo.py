import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.inspection import Inspection, InspectionImage, ImageCategory, OverallStatus
from app.schemas.inspection import InspectionOut
from app.services.demo_service import generate_demo_case, DEMO_CASES
from app.services.inspection_service import generate_inspection_code, run_full_analysis

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/cases")
def list_demo_cases():
    return {"demo_mode": settings.DEMO_MODE, "cases": DEMO_CASES}


@router.post("/{case_key}/run", response_model=InspectionOut)
def run_demo_case(case_key: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if case_key not in DEMO_CASES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown demo case")

    demo_image_path = generate_demo_case(case_key)
    meta = DEMO_CASES[case_key]

    inspection = Inspection(
        inspection_code=generate_inspection_code(),
        product_name=meta["product_name"],
        brand=meta["brand"],
        category=meta["category"],
        location="DEMO MODE - Sample Case",
        notes="Generated via PARAKH DEMO MODE for presentation/testing purposes.",
        officer_id=current_user.id,
        status=OverallStatus.PENDING,
        is_demo=True,
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    upload_dir = os.path.join(settings.UPLOAD_DIR, f"inspection_{inspection.id}")
    os.makedirs(upload_dir, exist_ok=True)
    dest_path = os.path.join(upload_dir, os.path.basename(demo_image_path))
    shutil.copy(demo_image_path, dest_path)

    image = InspectionImage(inspection_id=inspection.id, category=ImageCategory.FRONT, original_path=dest_path)
    db.add(image)
    db.commit()

    inspection = db.query(Inspection).filter(Inspection.id == inspection.id).first()
    run_full_analysis(db, inspection)
    return inspection
