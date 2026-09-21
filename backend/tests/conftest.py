import os
import tempfile
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["REPORT_DIR"] = tempfile.mkdtemp()

from app.core.database import Base, engine, SessionLocal  # noqa: E402
import app.models  # noqa: E402, F401 - import first so metadata sees all models
from app.main import app  # noqa: E402 - import LAST: must not be shadowed by `import app.xxx`
from app.core.security import hash_password  # noqa: E402
from app.models.user import User, RoleEnum  # noqa: E402
from app.seed import seed_rules  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(User(
        officer_id="TESTADMIN", email="admin@test.com", full_name="Test Admin",
        hashed_password=hash_password("Test@123"), role=RoleEnum.ADMIN,
    ))
    db.add(User(
        officer_id="TESTOFFICER", email="officer@test.com", full_name="Test Officer",
        hashed_password=hash_password("Test@123"), role=RoleEnum.OFFICER,
    ))
    db.commit()
    seed_rules(db)
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    r = client.post("/api/auth/login", json={"officer_id": "TESTADMIN", "password": "Test@123"})
    return r.json()["access_token"]


@pytest.fixture
def officer_token(client):
    r = client.post("/api/auth/login", json={"officer_id": "TESTOFFICER", "password": "Test@123"})
    return r.json()["access_token"]
