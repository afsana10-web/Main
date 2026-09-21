import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.inspection import Inspection, InspectionImage, ImageCategory, OverallStatus
from app.schemas.inspection import InspectionCreate, InspectionOut, InspectionListItem
from app.services.inspection_service import generate_inspection_code, run_full_analysis

router = APIRouter(prefix="/api/inspections", tags=["inspections"])


@router.post("", response_model=InspectionOut)
def create_inspection(
    payload: InspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = Inspection(
        inspection_code=generate_inspection_code(),
        product_name=payload.product_name,
        brand=payload.brand,
        category=payload.category,
        location=payload.location,
        notes=payload.notes,
        officer_id=current_user.id,
        status=OverallStatus.PENDING,
        is_demo=payload.is_demo,
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.post("/{inspection_id}/images")
def upload_images(
    inspection_id: int,
    files: list[UploadFile] = File(...),
    categories: list[str] = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")
    if len(files) != len(categories):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "files and categories length mismatch")

    saved = []
    upload_dir = os.path.join(settings.UPLOAD_DIR, f"inspection_{inspection.id}")
    os.makedirs(upload_dir, exist_ok=True)

    for file, category in zip(files, categories):
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported file type: {file.content_type}")

        contents_len = 0
        dest_path = os.path.join(upload_dir, file.filename)
        with open(dest_path, "wb") as f:
            while chunk := file.file.read(1024 * 1024):
                contents_len += len(chunk)
                if contents_len > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    f.close()
                    os.remove(dest_path)
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, "File too large")
                f.write(chunk)

        try:
            cat_enum = ImageCategory(category.upper())
        except ValueError:
            cat_enum = ImageCategory.OTHER

        image = InspectionImage(
            inspection_id=inspection.id,
            category=cat_enum,
            original_path=dest_path,
        )
        db.add(image)
        saved.append(image)

    db.commit()
    for img in saved:
        db.refresh(img)
    return {"uploaded": [{"id": i.id, "category": i.category.value, "path": i.original_path} for i in saved]}


@router.post("/{inspection_id}/analyze", response_model=InspectionOut)
def analyze_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = (
        db.query(Inspection)
        .options(joinedload(Inspection.images))
        .filter(Inspection.id == inspection_id)
        .first()
    )
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")
    if not inspection.images:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No images uploaded for this inspection")

    inspection.status = OverallStatus.PROCESSING
    db.commit()

    try:
        run_full_analysis(db, inspection)
    except Exception as e:
        import traceback
        traceback.print_exc()

        inspection.status = OverallStatus.FAILED
        db.commit()

        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Analysis failed: {e}"
        )

    return inspection


@router.get("", response_model=list[InspectionListItem])
def list_inspections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    officer_id: int | None = Query(None),
):
    q = db.query(Inspection)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(
            Inspection.product_name.ilike(like),
            Inspection.brand.ilike(like),
            Inspection.inspection_code.ilike(like),
        ))
    if status_filter:
        q = q.filter(Inspection.status == status_filter)
    if category:
        q = q.filter(Inspection.category.ilike(f"%{category}%"))
    if officer_id:
        q = q.filter(Inspection.officer_id == officer_id)
    return q.order_by(Inspection.created_at.desc()).all()


@router.get("/{inspection_id}", response_model=InspectionOut)
def get_inspection(
    inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found")
    return inspection
