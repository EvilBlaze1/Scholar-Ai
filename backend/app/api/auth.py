import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo.errors import PyMongoError

from app.schemas import UserCreate, UserLogin
from app.services.auth_service import (
    register_user,
    login_user
)
from app.database.user_repository import get_user_by_id
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


security = HTTPBearer()


@router.post("/register")
def register(user: UserCreate):
    try:
        result = register_user(
            user.email,
            user.password
        )
    except PyMongoError as exc:
        logger.error("Database connection error during registration: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. Please check MongoDB Atlas connection."
        )

    if result.get("error"):
        raise HTTPException(
            status_code=409,
            detail=result["error"]
        )

    return result


@router.post("/login")
def login(user: UserLogin):
    try:
        result = login_user(
            user.email,
            user.password
        )
    except PyMongoError as exc:
        logger.error("Database connection error during login: %s", exc)
        err_str = str(exc)
        hint = "Please check MongoDB Atlas connection."
        if "timeout" in err_str.lower() or "serverselection" in type(exc).__name__.lower():
            hint = "Connection timed out. In MongoDB Atlas, go to 'Network Access' and ensure your IP is whitelisted (or add 0.0.0.0/0)."
        elif "ssl" in err_str.lower() or "certificate" in err_str.lower():
            hint = "SSL Certificate error during TLS handshake."
        elif "authentication" in err_str.lower():
            hint = "Authentication failed. Check your database username/password in .env."

        raise HTTPException(
            status_code=503,
            detail=f"Database service unavailable. {hint}"
        )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return result


@router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    email = None
    try:
        user = get_user_by_id(user_id)
        if user:
            email = user.get("email")
    except Exception as exc:
        logger.debug("Could not fetch user record in /me: %s", exc)

    return {
        "user_id": user_id,
        "email": email
    }
