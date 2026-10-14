from app.database.user_repository import (
    create_user,
    get_user_by_email,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


def register_user(email: str, password: str):
    existing_user = get_user_by_email(email)

    if existing_user:
        return {
            "error": "Email already registered"
        }

    hashed_password = hash_password(password)

    user = create_user({
        "email": email,
        "password_hash": hashed_password,
    })

    return user


def login_user(email: str, password: str):
    user = get_user_by_email(email)

    if user is None:
        return None

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    token = create_access_token(
        str(user["_id"])
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }