import os

os.environ["JWT_SECRET"] = "test-secret"
os.environ["DATABASE_URL"] = "sqlite://"

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401
from app.db import Base, engine, state  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    state["initialized"] = True


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def headers():
    def build(user_id=1, household_id=1, name="Alice"):
        token = jwt.encode(
            {"sub": str(user_id), "household_id": household_id, "name": name},
            "test-secret",
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    return build
