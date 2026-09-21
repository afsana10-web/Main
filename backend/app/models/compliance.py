import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CheckStatus(str, enum.Enum):
    PASS = "PASS"
    POTENTIAL_NON_COMPLIANCE = "POTENTIAL_NON_COMPLIANCE"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), index=True)
    inspection = relationship("Inspection", back_populates="checks")

    rule_id: Mapped[int] = mapped_column(ForeignKey("compliance_rules.id"), index=True)
    rule_version: Mapped[str] = mapped_column(String(30))
    declaration_id: Mapped[int | None] = mapped_column(ForeignKey("declarations.id"), nullable=True)

    declaration_field: Mapped[str] = mapped_column(String(80))
    detected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CheckStatus] = mapped_column(Enum(CheckStatus), index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    finding = relationship("Finding", back_populates="check", uselist=False, cascade="all, delete-orphan")


class Finding(Base):
    """A finding is generated for any check that is not a clean PASS /
    NOT_APPLICABLE. It links to evidence and to officer verification."""
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), index=True)
    inspection = relationship("Inspection", back_populates="findings")

    check_id: Mapped[int] = mapped_column(ForeignKey("compliance_checks.id"), unique=True)
    check = relationship("ComplianceCheck", back_populates="finding")

    title: Mapped[str] = mapped_column(String(255))
    expected: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # LOW/MEDIUM/HIGH - triage aid only
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evidence = relationship("Evidence", back_populates="finding", uselist=False, cascade="all, delete-orphan")
    verification = relationship("VerificationRecord", back_populates="finding", uselist=False, cascade="all, delete-orphan")


class EvidenceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), unique=True)
    finding = relationship("Finding", back_populates="evidence")

    source_image_id: Mapped[int | None] = mapped_column(ForeignKey("inspection_images.id"), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[EvidenceStatus] = mapped_column(Enum(EvidenceStatus), default=EvidenceStatus.NOT_AVAILABLE)
    bbox_x: Mapped[int | None] = mapped_column(nullable=True)
    bbox_y: Mapped[int | None] = mapped_column(nullable=True)
    bbox_width: Mapped[int | None] = mapped_column(nullable=True)
    bbox_height: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
