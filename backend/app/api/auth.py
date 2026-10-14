from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas import UserCreate, UserLogin
from app.services.auth_service import (
    register_user,
    login_user
)
from app.core.security import decode_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


security = HTTPBearer()


@router.post("/register")
def register(user: UserCreate):

    result = register_user(
        user.email,
        user.password
    )

    if result.get("error"):
        raise HTTPException(
            status_code=409,
            detail=result["error"]
        )

    return result


@router.post("/login")
def login(user: UserLogin):

    result = login_user(
        user.email,
        user.password
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

    return {
        "user_id": user_id
    }