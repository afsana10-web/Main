import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class OverallStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLIANT = "COMPLIANT"
    POTENTIAL_NON_COMPLIANCE = "POTENTIAL_NON_COMPLIANCE"
    NEEDS_OFFICER_VERIFICATION = "NEEDS_OFFICER_VERIFICATION"
    FAILED = "FAILED"


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    product_name: Mapped[str] = mapped_column(String(255), index=True)
    brand: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    location: Mapped[str] = mapped_column(String(255))
    inspection_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    officer = relationship("User", back_populates="inspections")

    status: Mapped[OverallStatus] = mapped_column(
        Enum(OverallStatus), default=OverallStatus.PENDING, index=True
    )
    ruleset_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_demo: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    declarations = relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")
    checks = relationship("ComplianceCheck", back_populates="inspection", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")


class ImageCategory(str, enum.Enum):
    FRONT = "FRONT"
    BACK = "BACK"
    SIDE = "SIDE"
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    OTHER = "OTHER"


class ImageQuality(str, enum.Enum):
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    POOR = "POOR"
    UNKNOWN = "UNKNOWN"


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), index=True)
    inspection = relationship("Inspection", back_populates="images")

    category: Mapped[ImageCategory] = mapped_column(Enum(ImageCategory), default=ImageCategory.OTHER)
    original_path: Mapped[str] = mapped_column(String(500))
    preprocessed_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality: Mapped[ImageQuality] = mapped_column(Enum(ImageQuality), default=ImageQuality.UNKNOWN)
    quality_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ocr_result = relationship("OCRResult", back_populates="image", uselist=False, cascade="all, delete-orphan")
