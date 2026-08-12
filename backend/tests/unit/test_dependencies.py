from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user


def test_get_current_user_rejects_invalid_token():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token",
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401