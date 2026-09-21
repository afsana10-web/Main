"""
Run with: python -m app.seed
Creates all tables (for the SQLite demo path - use Alembic migrations for
PostgreSQL in real deployments), seeds the rule set from
compliance-rules/rules.json, and creates two demo users (admin + officer).
"""
import json
import os
from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.core.config import settings
import app.models  # noqa: F401 - ensures all models are registered on Base.metadata
from app.models.user import User, RoleEnum
from app.models.rule import ComplianceRule, RuleStatus


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_rules(db):
    if db.query(ComplianceRule).count() > 0:
        print("Rules already seeded, skipping.")
        return

    rules_path = os.path.join(os.path.dirname(__file__), "..", settings.RULES_CONFIG_PATH)
    rules_path = os.path.normpath(rules_path)
    with open(rules_path) as f:
        data = json.load(f)

    for r in data["rules"]:
        rule = ComplianceRule(
            rule_code=r["rule_code"],
            rule_name=r["rule_name"],
            category=r["category"],
            applicable_condition=r.get("applicable_condition"),
            validation_method=r["validation_method"],
            validation_params=json.dumps(r.get("validation_params", {})),
            reason_template=r["reason_template"],
            version=data["version"],
            legal_reference=r.get("legal_reference"),
            status=RuleStatus(r.get("status", "ACTIVE")),
        )
        db.add(rule)
    db.commit()
    print(f"Seeded {len(data['rules'])} compliance rules (version {data['version']}).")


def seed_users(db):
    if db.query(User).count() > 0:
        print("Users already seeded, skipping.")
        return

    admin = User(
        officer_id="ADMIN001",
        email="admin@parakh.gov.in",
        full_name="System Administrator",
        hashed_password=hash_password("Admin@123"),
        role=RoleEnum.ADMIN,
    )
    officer = User(
        officer_id="OFF1001",
        email="officer1@parakh.gov.in",
        full_name="Inspector Priya Sharma",
        hashed_password=hash_password("Officer@123"),
        role=RoleEnum.OFFICER,
    )
    db.add_all([admin, officer])
    db.commit()
    print("Seeded demo users: ADMIN001 / Admin@123 (ADMIN), OFF1001 / Officer@123 (OFFICER)")


def main():
    create_tables()
    db = SessionLocal()
    try:
        seed_rules(db)
        seed_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
