from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.user import User


client = TestClient(app)


def override_get_db():
    yield None


def override_get_current_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="not-used",
        role_id=1,
    )


app.dependency_overrides[get_db] = override_get_db


def teardown_module():
    app.dependency_overrides.clear()


def test_auth_me_requires_authentication():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_auth_me_with_authenticated_user():
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["role_id"] == 1
    assert "password_hash" not in data