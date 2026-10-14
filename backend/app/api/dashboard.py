from fastapi import APIRouter, Depends, HTTPException

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from app.core.security import decode_access_token
from app.services.dashboard_service import get_user_dashboard


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = decode_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user_id


@router.get("/me")
def dashboard(
    user_id: str = Depends(get_current_user_id)
):
    result = get_user_dashboard(user_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found"
        )

    return result