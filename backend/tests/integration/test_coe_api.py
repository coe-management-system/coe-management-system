from unittest.mock import MagicMock
import pytest
from app.api.routes.coe import faculty_required
from fastapi.testclient import TestClient
from app.core.database import get_db
from app.main import app
from app.models.coe import CoE
from app.models.coe_lab import CoELab
from app.models.user import User


client = TestClient(app)

mock_db = MagicMock()


def refresh_side_effect(obj):
    if isinstance(obj, CoE):
        obj.id = 1
    elif isinstance(obj, CoELab):
        obj.id = 1


mock_db.refresh.side_effect = refresh_side_effect


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




def test_create_coe():
    mock_db.reset_mock()

    response = client.post(
        "/api/v1/coe",
        json={
            "name": "Cloud Computing CoE",
            "status": "active",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Cloud Computing CoE"
    assert data["status"] == "active"


def test_get_coes():
    mock_db.reset_mock()

    response = client.get(
        "/api/v1/coe",
    )

    assert response.status_code == 200


def test_create_coe_lab():
    mock_db.reset_mock()

    response = client.post(
        "/api/v1/coe/labs",
        json={
            "coe_id": 1,
            "name": "Cloud Lab",
            "location": "Block A",
            "capacity": 30,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["coe_id"] == 1
    assert data["name"] == "Cloud Lab"


def test_get_coe_not_found():
    mock_db.reset_mock()

    mock_db.get.return_value = None

    response = client.get(
        "/api/v1/coe/999999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "CoE not found"