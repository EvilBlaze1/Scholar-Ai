import pytest
import bcrypt
from unittest.mock import MagicMock, patch

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import login_user, register_user
from app.database import user_repository


def test_argon2_hash_and_verify():
    pwd = "student_secret_pass_123"
    hashed = hash_password(pwd)
    assert hashed.startswith("$argon2")
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_bcrypt_hash_verification_fallback():
    pwd = "existing_student_bcrypt_pass"
    # Generate a standard $2b$ bcrypt hash as stored by older backends
    b_hash = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    assert b_hash.startswith("$2b$")

    # verify_password MUST verify bcrypt successfully without UnknownHashError
    assert verify_password(pwd, b_hash) is True
    assert verify_password("different_pass", b_hash) is False


def test_corrupted_hash_does_not_crash():
    # Corrupted / invalid hash string must return False without raising UnknownHashError
    assert verify_password("password123", "not_a_valid_hash_string") is False
    assert verify_password("password123", "$unknown$hash$format") is False
    assert verify_password("", "some_hash") is False
    assert verify_password("password123", "") is False
    assert verify_password(None, None) is False


def test_user_login_schema_whitespace_and_case_cleaning():
    payload = {
        "email": "  Student.College@GMAIL.com  ",
        "password": "my_password_123"
    }
    schema = UserLogin(**payload)
    assert schema.email == "student.college@gmail.com"
    assert schema.password == "my_password_123"


def test_user_create_schema_whitespace_and_case_cleaning():
    payload = {
        "email": "  NewStudent@Example.Org  ",
        "password": "secure_password_123"
    }
    schema = UserCreate(**payload)
    assert schema.email == "newstudent@example.org"
    assert schema.password == "secure_password_123"


def test_case_insensitive_email_lookup():
    mock_collection = MagicMock()
    # When user registered as "Student@Example.com" and searches with mixed case:
    # 1. Exact match -> None
    # 2. Lowercase match -> None
    # 3. Regex match -> Found
    mock_collection.find_one.side_effect = [None, None, {"email": "Student@Example.com", "_id": "123"}]

    with patch.object(user_repository, "users_collection", mock_collection):
        user = user_repository.get_user_by_email("Student@Example.COM")
        assert user is not None
        assert user["email"] == "Student@Example.com"
        assert mock_collection.find_one.call_count == 3


def test_login_user_with_bcrypt_and_auto_rehash():
    user_id = "507f1f77bcf86cd799439011"
    raw_pass = "my_valid_password"
    b_hash = bcrypt.hashpw(raw_pass.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    mock_user = {
        "_id": user_id,
        "email": "student@example.com",
        "password_hash": b_hash,
    }

    with patch("app.services.auth_service.get_user_by_email", return_value=mock_user), \
         patch("app.services.auth_service.update_user_password") as mock_update_pw:
        res = login_user("Student@Example.COM", raw_pass)
        assert res is not None
        assert "access_token" in res
        assert res["user"]["email"] == "student@example.com"
        # Auto-rehash was triggered for legacy bcrypt hash
        assert mock_update_pw.called
        call_args = mock_update_pw.call_args[0]
        assert call_args[0] == user_id
        assert call_args[1].startswith("$argon2")


def test_login_user_invalid_credentials():
    mock_user = {
        "_id": "507f1f77bcf86cd799439011",
        "email": "student@example.com",
        "password_hash": hash_password("correct_password"),
    }

    with patch("app.services.auth_service.get_user_by_email", return_value=mock_user):
        res = login_user("student@example.com", "wrong_password")
        assert res is None

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        res = login_user("nonexistent@example.com", "any_password")
        assert res is None
