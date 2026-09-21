import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class OfficerDecision(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class VerificationRecord(Base):
    """Stores the officer's decision SEPARATELY from the automated finding.
    The automated result (on Finding/ComplianceCheck) is never overwritten."""
    __tablename__ = "verification_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), unique=True)
    finding = relationship("Finding", back_populates="verification")

    officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[OfficerDecision] = mapped_column(Enum(OfficerDecision))
    corrected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
