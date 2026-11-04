import logging
from app.database.user_repository import (
    create_user,
    get_user_by_email,
    update_user_password,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

logger = logging.getLogger(__name__)


def register_user(email: str, password: str):
    clean_email = email.strip().lower()

    existing_user = get_user_by_email(clean_email)
    if existing_user:
        return {
            "error": "Email already registered"
        }

    hashed_password = hash_password(password)

    user = create_user({
        "email": clean_email,
        "password_hash": hashed_password,
    })

    return user


def login_user(email: str, password: str):
    if not email or not password:
        return None

    clean_email = email.strip().lower()
    user = get_user_by_email(clean_email)

    if user is None:
        logger.info("Login attempt failed: user with email '%s' not found", clean_email)
        return None

    stored_hash = user.get("password_hash")
    if not stored_hash or not verify_password(password, stored_hash):
        logger.info("Login attempt failed: invalid password for user '%s'", clean_email)
        return None

    # Transparent upgrade for legacy password hashes to modern Argon2
    try:
        if str(stored_hash).startswith(("$2a$", "$2b$", "$2y$", "$2x$")):
            new_hash = hash_password(password)
            update_user_password(str(user["_id"]), new_hash)
            logger.info("Transparently migrated password hash to Argon2 for user '%s'", clean_email)
    except Exception as exc:
        logger.debug("Password hash migration skipped: %s", exc)

    token = create_access_token(
        str(user["_id"])
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user.get("email", clean_email),
        }
    }
