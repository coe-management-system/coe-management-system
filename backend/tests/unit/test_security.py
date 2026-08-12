import jwt

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "TestPassword123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("WrongPassword", hashed_password)


def test_create_and_decode_access_token():
    token = create_access_token("123")

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload


def test_invalid_token_is_rejected():
    invalid_token = "invalid.jwt.token"

    try:
        decode_access_token(invalid_token)
        assert False, "Invalid token should have been rejected"
    except jwt.InvalidTokenError:
        pass