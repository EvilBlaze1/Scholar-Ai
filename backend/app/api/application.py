
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator

from app.core.security import decode_access_token
from app.services.application_service import (
    add_application,
    fetch_user_applications,
    change_application_status,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)

security = HTTPBearer()

VALID_STATUSES = {
    "NOT_APPLIED",
    "APPLIED",
    "UNDER_REVIEW",
    "SELECTED",
    "REJECTED",
}


class ApplicationCreate(BaseModel):
    scholarship_id: str = Field(min_length=1, max_length=2048)
    status: str = "APPLIED"
    notes: str | None = Field(default=None, max_length=2000)
    applied_at: str | None = Field(default=None, max_length=50)

    @field_validator("scholarship_id")
    @classmethod
    def validate_scholarship_id(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Scholarship ID cannot be empty")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        value = value.strip().upper()
        if value not in VALID_STATUSES:
            raise ValueError("Invalid application status")
        return value


class ApplicationStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        value = value.strip().upper()
        if value not in VALID_STATUSES:
            raise ValueError("Invalid application status")
        return value


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = decode_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return user_id


@router.post("/")
def create_application(
    application: ApplicationCreate,
    user_id: str = Depends(get_current_user_id),
):
    result = add_application(
        user_id=user_id,
        scholarship_id=application.scholarship_id,
        status=application.status,
        notes=application.notes,
        applied_at=application.applied_at,
    )

    if result.get("error"):
        message = result["error"]

        if message == "Application already exists":
            status_code = 409
        elif message == "Invalid application status":
            status_code = 422
        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    return result


@router.get("/")
def get_applications(
    user_id: str = Depends(get_current_user_id),
):
    return fetch_user_applications(user_id)


@router.put("/{scholarship_id}")
def update_application_status(
    scholarship_id: str,
    application: ApplicationStatusUpdate,
    user_id: str = Depends(get_current_user_id),
):
    if not scholarship_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Scholarship ID is required",
        )

    result = change_application_status(
        user_id=user_id,
        scholarship_id=scholarship_id,
        status=application.status,
    )

    if result.get("error"):
        message = result["error"]

        if message == "Application not found":
            status_code = 404
        elif message == "Invalid application status":
            status_code = 422
        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    return result
