from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing_and_verification():
    plain = "MySecretPassword123"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = "test_user_67890"
    token = create_access_token(user_id)

    assert isinstance(token, str)
    decoded_id = decode_access_token(token)
    assert decoded_id == user_id


def test_jwt_invalid_token():
    invalid_token = "invalid.token.string"
    assert decode_access_token(invalid_token) is None
