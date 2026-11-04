import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")

if not SECRET_KEY:
    SECRET_KEY = "scholar-ai-dev-secret-key-for-local-fallback-only"


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for stable session persistence

# Multi-hasher: Argon2 (recommended default for hashing) + Bcrypt (for existing legacy hashes)
password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))


def hash_password(password: str) -> str:
    """Hash password using modern Argon2 algorithm."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify password against hashed password.
    Supports Argon2, bcrypt ($2a$, $2b$, $2y$), passlib fallback, and development fallback.
    Never raises an unhandled exception on malformed or legacy hashes.
    """
    if not plain_password or not hashed_password:
        return False

    plain_str = str(plain_password)
    hashed_str = str(hashed_password).strip()

    # 1. Primary check via pwdlib multi-hasher (Argon2 + Bcrypt)
    try:
        if password_hash.verify(plain_str, hashed_str):
            return True
    except Exception as exc:
        logger.debug("pwdlib verification failed: %s", exc)

    # 2. Direct bcrypt check fallback for legacy bcrypt prefixes ($2a$, $2b$, $2y$, $2x$)
    if hashed_str.startswith(("$2a$", "$2b$", "$2y$", "$2x$")):
        try:
            if bcrypt.checkpw(plain_str.encode("utf-8"), hashed_str.encode("utf-8")):
                return True
        except Exception as exc:
            logger.debug("Direct bcrypt checkpw failed: %s", exc)

    # 3. Fallback for passlib CryptContext if hash format is passlib-specific
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(
            schemes=["bcrypt", "argon2", "pbkdf2_sha256", "sha256_crypt"],
            deprecated="auto"
        )
        if pwd_context.verify(plain_str, hashed_str):
            return True
    except Exception:
        pass

    # 4. Safe plain text fallback in development / test environments only
    if os.getenv("ENVIRONMENT") == "development" and hashed_str == plain_str:
        return True

    return False


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return str(user_id)

    except JWTError:
        return None
    except Exception:
        return None
