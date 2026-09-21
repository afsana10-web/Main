from datetime import datetime
from pydantic import BaseModel
from app.models.inspection import OverallStatus, ImageCategory, ImageQuality


class InspectionCreate(BaseModel):
    product_name: str
    brand: str
    category: str
    location: str
    notes: str | None = None
    is_demo: bool = False


class InspectionImageOut(BaseModel):
    id: int
    category: ImageCategory
    original_path: str
    preprocessed_path: str | None
    width: int | None
    height: int | None
    quality: ImageQuality
    quality_reason: str | None

    class Config:
        from_attributes = True


class InspectionOut(BaseModel):
    id: int
    inspection_code: str
    product_name: str
    brand: str
    category: str
    location: str
    inspection_date: datetime
    notes: str | None
    officer_id: int
    status: OverallStatus
    ruleset_version: str | None
    is_demo: bool
    created_at: datetime
    analyzed_at: datetime | None
    verified_at: datetime | None
    images: list[InspectionImageOut] = []

    class Config:
        from_attributes = True


class InspectionListItem(BaseModel):
    id: int
    inspection_code: str
    product_name: str
    brand: str
    category: str
    inspection_date: datetime
    status: OverallStatus
    officer_id: int

    class Config:
        from_attributes = True
