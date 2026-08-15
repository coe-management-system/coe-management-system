from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.routes.company import faculty_required
from app.core.database import get_db
from app.main import app
from app.models.company import Company
from app.models.user import User


client = TestClient(app)

mock_db = MagicMock()


def override_get_db():
    yield mock_db


def override_faculty_user():
    return User(
        id=1,
        role_id=1,
    )


def refresh_side_effect(obj):
    if isinstance(obj, Company):
        obj.id = 1


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[faculty_required] = override_faculty_user

    yield

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(faculty_required, None)


def reset_mock_db():
    mock_db.reset_mock(
        return_value=True,
        side_effect=True,
    )

    mock_db.refresh.side_effect = refresh_side_effect


def test_create_company():
    reset_mock_db()

    response = client.post(
        "/api/v1/companies",
        json={
            "name": "Amazon Web Services",
            "type": "Technology",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Amazon Web Services"
    assert data["type"] == "Technology"


def test_get_companies():
    reset_mock_db()

    response = client.get(
        "/api/v1/companies",
    )

    assert response.status_code == 200


def test_get_company_not_found():
    reset_mock_db()

    mock_db.get.return_value = None

    response = client.get(
        "/api/v1/companies/999999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"