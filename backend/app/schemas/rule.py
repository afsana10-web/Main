from datetime import datetime
from pydantic import BaseModel
from app.models.rule import RuleStatus


class RuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    category: str
    applicable_condition: str | None = None
    validation_method: str
    validation_params: str | None = None
    reason_template: str
    version: str
    legal_reference: str | None = None
    status: RuleStatus = RuleStatus.ACTIVE


class RuleUpdate(BaseModel):
    rule_name: str | None = None
    applicable_condition: str | None = None
    validation_method: str | None = None
    validation_params: str | None = None
    reason_template: str | None = None
    version: str | None = None
    legal_reference: str | None = None
    status: RuleStatus | None = None


class RuleOut(BaseModel):
    id: int
    rule_code: str
    rule_name: str
    category: str
    applicable_condition: str | None
    validation_method: str
    validation_params: str | None
    reason_template: str
    version: str
    status: RuleStatus
    legal_reference: str | None
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    officer_id: str
    email: str
    full_name: str
    password: str
    role: str = "OFFICER"


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None
