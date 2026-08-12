from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.dependencies import require_role
from app.models.role import Role
from app.models.user import User


def test_require_role_allows_matching_role():
    user = User(
        id=1,
        username="admin",
        email="admin@coe.local",
        password_hash="not-used",
        role_id=1,
    )

    role = Role(
        id=1,
        name="admin",
    )

    db = MagicMock()
    db.scalar.return_value = role

    dependency = require_role("admin")

    result = dependency(
        current_user=user,
        db=db,
    )

    assert result is user


def test_require_role_rejects_wrong_role():
    user = User(
        id=1,
        username="faculty",
        email="faculty@coe.local",
        password_hash="not-used",
        role_id=2,
    )

    role = Role(
        id=2,
        name="faculty",
    )

    db = MagicMock()
    db.scalar.return_value = role

    dependency = require_role("admin")

    with pytest.raises(HTTPException) as exc_info:
        dependency(
            current_user=user,
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"

def test_require_role_rejects_missing_role():
    user = User(
        id=1,
        username="admin",
        email="admin@coe.local",
        password_hash="not-used",
        role_id=999,
    )

    db = MagicMock()
    db.scalar.return_value = None

    dependency = require_role("admin")

    with pytest.raises(HTTPException) as exc_info:
        dependency(
            current_user=user,
            db=db,
        )

    assert exc_info.value.status_code == 403