from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("inspection_images.id"), unique=True, index=True)
    image = relationship("InspectionImage", back_populates="ocr_result")

    full_text: Mapped[str] = mapped_column(Text)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    engine: Mapped[str] = mapped_column(String(50), default="tesseract")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    words = relationship("OCRWord", back_populates="ocr_result", cascade="all, delete-orphan")


class OCRWord(Base):
    """Word-level OCR output with bounding box, as returned by pytesseract's
    image_to_data. Bounding boxes are only ever stored when Tesseract actually
    produced them - never fabricated."""
    __tablename__ = "ocr_words"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ocr_result_id: Mapped[int] = mapped_column(ForeignKey("ocr_results.id"), index=True)
    ocr_result = relationship("OCRResult", back_populates="words")

    text: Mapped[str] = mapped_column(String(500))
    confidence: Mapped[float] = mapped_column(Float)
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    line_num: Mapped[int] = mapped_column(Integer, default=0)
    word_num: Mapped[int] = mapped_column(Integer, default=0)
