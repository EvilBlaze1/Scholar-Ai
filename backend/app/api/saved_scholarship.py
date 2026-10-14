
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, HttpUrl

from app.core.security import decode_access_token
from app.services.saved_scholarship_service import (
    add_saved_scholarship,
    fetch_saved_scholarships,
    remove_saved_scholarship,
)


router = APIRouter(
    prefix="/saved-scholarships",
    tags=["Saved Scholarships"],
)

security = HTTPBearer()


class SaveScholarshipRequest(BaseModel):
    scholarship: dict[str, Any] | None = None


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


@router.post("/{scholarship_id}")
def save_scholarship(
    scholarship_id: str,
    payload: SaveScholarshipRequest | None = None,
    user_id: str = Depends(get_current_user_id),
):
    if not scholarship_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Scholarship ID is required",
        )

    scholarship_data = payload.scholarship if payload else None

    if scholarship_data is not None:
        source_url = scholarship_data.get("source_url")
        item_id = scholarship_data.get("id")

        # The submitted snapshot must refer to the item being saved.
        if item_id and item_id != scholarship_id:
            raise HTTPException(
                status_code=400,
                detail="Scholarship ID does not match the submitted data",
            )

        # Validate source URLs when provided.
        if source_url is not None:
            try:
                parsed_url = HttpUrl(source_url)
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid scholarship source URL",
                ) from exc

            if parsed_url.scheme not in ("http", "https"):
                raise HTTPException(
                    status_code=400,
                    detail="Scholarship source URL must use HTTP or HTTPS",
                )

    result = add_saved_scholarship(
        user_id,
        scholarship_id,
        scholarship_data,
    )

    if result and result.get("already_saved"):
        return result

    if result is None:
        # Backward compatibility for any repository implementation
        # that still returns None for duplicate saves.
        existing = fetch_saved_scholarships(user_id)
        for item in existing:
            if item.get("scholarship_id") == scholarship_id:
                return item

        raise HTTPException(
            status_code=409,
            detail="Could not save scholarship",
        )

    return result


@router.get("/")
def get_saved_scholarships(
    user_id: str = Depends(get_current_user_id),
):
    return fetch_saved_scholarships(user_id)


@router.delete("/{scholarship_id}")
def delete_saved_scholarship(
    scholarship_id: str,
    user_id: str = Depends(get_current_user_id),
):
    deleted = remove_saved_scholarship(user_id, scholarship_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Saved scholarship not found",
        )

    return {"message": "Scholarship removed from saved list"}
