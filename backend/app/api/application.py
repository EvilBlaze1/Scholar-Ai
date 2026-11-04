from typing import Any, Union
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator

from app.core.security import decode_access_token
from app.services.application_service import (
    add_application,
    fetch_user_applications,
    change_application_status,
    update_user_application,
    remove_application,
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
    scholarship_name: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, max_length=255)
    scholarship_amount: Union[str, float, int, None] = None

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


class ApplicationUpdateRequest(BaseModel):
    status: str | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value is not None:
            value = value.strip().upper()
            if value not in VALID_STATUSES:
                raise ValueError("Invalid application status")
        return value


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    user_id = decode_access_token(token)

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
        scholarship_name=application.scholarship_name,
        provider=application.provider,
        scholarship_amount=application.scholarship_amount,
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
def get_my_applications(
    user_id: str = Depends(get_current_user_id),
):
    return fetch_user_applications(user_id)


@router.patch("/{scholarship_id}/status")
def update_status(
    scholarship_id: str,
    update: ApplicationStatusUpdate,
    user_id: str = Depends(get_current_user_id),
):
    result = change_application_status(
        user_id=user_id,
        scholarship_id=scholarship_id,
        status=update.status,
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


@router.put("/{scholarship_id:path}")
def update_application_endpoint(
    scholarship_id: str,
    update: ApplicationUpdateRequest,
    user_id: str = Depends(get_current_user_id),
):
    result = update_user_application(
        user_id=user_id,
        scholarship_id=scholarship_id,
        status=update.status,
        notes=update.notes,
    )

    if result.get("error"):
        message = result["error"]
        status_code = (
            404
            if message == "Application not found"
            else (422 if message == "Invalid application status" else 400)
        )
        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    return result


@router.delete("/")
def delete_application_query(
    scholarship_id: str,
    user_id: str = Depends(get_current_user_id),
):
    return delete_application_endpoint(
        scholarship_id=scholarship_id,
        user_id=user_id,
    )


@router.delete("/{scholarship_id:path}")
def delete_application_endpoint(
    scholarship_id: str,
    user_id: str = Depends(get_current_user_id),
):
    result = remove_application(
        user_id=user_id,
        scholarship_id=scholarship_id,
    )

    if result.get("error"):
        raise HTTPException(
            status_code=404,
            detail=result["error"],
        )

    return result
