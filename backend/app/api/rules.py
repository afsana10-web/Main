import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.rule import ComplianceRule, RuleStatus
from app.schemas.rule import RuleCreate, RuleUpdate, RuleOut

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=list[RuleOut])
def list_rules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ComplianceRule).order_by(ComplianceRule.category).all()


@router.get("/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")
    return rule


@router.post("", response_model=RuleOut)
def create_rule(payload: RuleCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rule = ComplianceRule(
        rule_code=payload.rule_code,
        rule_name=payload.rule_name,
        category=payload.category,
        applicable_condition=payload.applicable_condition,
        validation_method=payload.validation_method,
        validation_params=payload.validation_params,
        reason_template=payload.reason_template,
        version=payload.version,
        legal_reference=payload.legal_reference,
        status=payload.status,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, payload: RuleUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def deactivate_rule(rule_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")
    # Soft-deactivate rather than hard delete, to preserve audit history for
    # past inspections that referenced this rule/version.
    rule.status = RuleStatus.INACTIVE
    db.commit()
    return {"detail": "Rule deactivated", "rule_id": rule_id}
