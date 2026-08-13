from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.models.user import User
from app.services.auth_service import AuthService


def test_authenticate_user_success():
    password = "TestPassword123"

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash=hash_password(password),
        role_id=1,
    )

    db = MagicMock()
    db.scalar.return_value = user

    authenticated_user = AuthService.authenticate_user(
        db=db,
        username="testuser",
        password=password,
    )

    assert authenticated_user is user


def test_authenticate_user_wrong_password():
    password = "TestPassword123"

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash=hash_password(password),
        role_id=1,
    )

    db = MagicMock()
    db.scalar.return_value = user

    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(
            db=db,
            username="testuser",
            password="WrongPassword",
        )

    assert exc_info.value.status_code == 401


def test_authenticate_user_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(
            db=db,
            username="does-not-exist",
            password="TestPassword123",
        )

    assert exc_info.value.status_code == 401