
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
    scholarship_id: str | None = None
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


@router.post("/")
def save_scholarship_root(
    payload: SaveScholarshipRequest,
    user_id: str = Depends(get_current_user_id),
):
    target_id = payload.scholarship_id
    if not target_id and payload.scholarship:
        target_id = (
            payload.scholarship.get("id") or
            payload.scholarship.get("scholarship_id") or
            payload.scholarship.get("source_url")
        )

    if not target_id or not str(target_id).strip():
        raise HTTPException(
            status_code=400,
            detail="Scholarship ID is required",
        )

    return save_scholarship(
        scholarship_id=str(target_id).strip(),
        payload=payload,
        user_id=user_id,
    )


@router.post("/{scholarship_id:path}")
def save_scholarship(
    scholarship_id: str,
    payload: SaveScholarshipRequest | None = None,
    user_id: str = Depends(get_current_user_id),
):
    scholarship_id = str(scholarship_id).strip()
    if not scholarship_id:
        raise HTTPException(
            status_code=400,
            detail="Scholarship ID is required",
        )

    scholarship_data = payload.scholarship if payload else None

    if isinstance(scholarship_data, dict):
        # Keep submitted ID aligned with path
        scholarship_data["id"] = scholarship_id

    result = add_saved_scholarship(
        user_id,
        scholarship_id,
        scholarship_data,
    )

    if result and result.get("already_saved"):
        return result

    if result is None:
        existing = fetch_saved_scholarships(user_id)
        for item in existing:
            if item.get("scholarship_id") == scholarship_id:
                return item

        raise HTTPException(
            status_code=409,
            detail="Could not save scholarship",
        )

    return result


@router.get("/ids")
def get_saved_ids(
    user_id: str = Depends(get_current_user_id),
):
    items = fetch_saved_scholarships(user_id) or []
    ids = set()
    for item in items:
        if item.get("scholarship_id"):
            ids.add(str(item["scholarship_id"]))
        if item.get("id"):
            ids.add(str(item["id"]))
        snap = item.get("scholarship")
        if isinstance(snap, dict):
            if snap.get("id"):
                ids.add(str(snap["id"]))
            if snap.get("source_url"):
                ids.add(str(snap["source_url"]))
    return {"saved_ids": list(ids)}


@router.get("/")
def get_saved_scholarships(
    user_id: str = Depends(get_current_user_id),
):
    return fetch_saved_scholarships(user_id)


@router.delete("/")
def delete_saved_scholarship_query(
    scholarship_id: str,
    user_id: str = Depends(get_current_user_id),
):
    return delete_saved_scholarship(
        scholarship_id=scholarship_id,
        user_id=user_id,
    )


@router.delete("/{scholarship_id:path}")
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

    return {
        "message": "Scholarship removed from saved list",
        "scholarship_id": scholarship_id,
    }
