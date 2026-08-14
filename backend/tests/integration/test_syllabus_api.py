from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.role import Role
from app.models.user import User


client = TestClient(app)


def override_get_db():
    db = MagicMock()

    db.scalar.return_value = Role(
        id=2,
        name="faculty",
    )

    yield db


def override_get_current_user():
    return User(
        id=1,
        username="faculty",
        email="faculty@test.com",
        password_hash="not-used",
        role_id=2,
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def teardown_module():
    app.dependency_overrides.clear()


def test_syllabus_routes_are_registered():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/syllabus" in paths
    assert "/api/v1/syllabus/{topic_id}" in paths


def test_syllabus_requires_authentication():
    app.dependency_overrides.clear()

    response = client.get("/api/v1/syllabus")

    assert response.status_code == 401

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user


def test_syllabus_create_validation():
    response = client.post(
        "/api/v1/syllabus",
        json={
            "subject_id": 101,
            "unit": "Unit 1",
            "topic": "Introduction",
            "planned_classes": 5,
            "completed_classes": 6,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Completed classes cannot exceed planned classes"
    )
