from unittest.mock import MagicMock
import pytest

from app.api.routes.technology import faculty_required
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import app
from app.models.user import User

from app.models.technology import Technology

client = TestClient(app)

mock_db = MagicMock()


def override_get_db():
    yield mock_db


def override_faculty_user():
    return User(
        id=1,
        role_id=1,
    )


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    yield

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(faculty_required, None)


def refresh_side_effect(obj):
    if isinstance(obj, Technology):
        obj.id = 1


mock_db.refresh.side_effect = refresh_side_effect


def test_create_technology():
    response = client.post(
        "/api/v1/technologies",
        json={
            "name": "AWS",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "AWS"


def test_get_technologies():
    response = client.get(
        "/api/v1/technologies",
    )

    assert response.status_code == 200


def test_get_technology_not_found():
    mock_db.reset_mock()
    mock_db.get.return_value = None

    response = client.get(
        "/api/v1/technologies/999999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Technology not found"