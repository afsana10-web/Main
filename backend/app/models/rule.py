import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RuleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAFT = "DRAFT"


class ComplianceRule(Base):
    """A single configurable rule. Rules are NOT hard-coded in application
    logic - the engine reads rows from this table (seeded from
    compliance-rules/rules.json) and applies them generically."""
    __tablename__ = "compliance_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_code: Mapped[str] = mapped_column(String(50), index=True)  # e.g. LMPC-NQ-01
    rule_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120), index=True)  # maps to DeclarationField
    applicable_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_method: Mapped[str] = mapped_column(String(100))  # e.g. REQUIRED_PRESENT, REGEX_MATCH, NUMERIC_RANGE
    validation_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    reason_template: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[RuleStatus] = mapped_column(Enum(RuleStatus), default=RuleStatus.ACTIVE, index=True)
    legal_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
