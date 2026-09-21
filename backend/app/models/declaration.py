import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DeclarationField(str, enum.Enum):
    MANUFACTURER_PACKER_IMPORTER = "MANUFACTURER_PACKER_IMPORTER"
    COUNTRY_OF_ORIGIN = "COUNTRY_OF_ORIGIN"
    PRODUCT_NAME = "PRODUCT_NAME"
    NET_QUANTITY = "NET_QUANTITY"
    MRP = "MRP"
    MFG_PACKING_IMPORT_DATE = "MFG_PACKING_IMPORT_DATE"
    BEST_BEFORE_USE_BY = "BEST_BEFORE_USE_BY"
    CONSUMER_CARE = "CONSUMER_CARE"
    UNIT_SALE_PRICE = "UNIT_SALE_PRICE"
    DIMENSIONS = "DIMENSIONS"


class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), index=True)
    inspection = relationship("Inspection", back_populates="declarations")

    field: Mapped[DeclarationField] = mapped_column(Enum(DeclarationField), index=True)
    detected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_image_id: Mapped[int | None] = mapped_column(ForeignKey("inspection_images.id"), nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # bounding box on the source image, only populated when genuinely available
    bbox_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_verification: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
