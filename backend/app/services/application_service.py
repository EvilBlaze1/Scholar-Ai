from datetime import datetime, timezone
from typing import Union

from app.database.application_repository import (
    create_application,
    get_user_applications,
    get_application,
    update_application,
    delete_application,
)
from app.database.scholarship_repository import get_scholarship


VALID_STATUSES = {
    "NOT_APPLIED",
    "APPLIED",
    "UNDER_REVIEW",
    "SELECTED",
    "REJECTED",
}

SUBMITTED_STATUSES = {
    "APPLIED",
    "UNDER_REVIEW",
    "SELECTED",
    "REJECTED",
}


def _now() -> str:
    """Return the current UTC time as an ISO-formatted string."""
    return datetime.now(timezone.utc).isoformat()


def _clean_optional_text(value: str | None) -> str | None:
    """Normalize optional text fields."""
    if value is None or not isinstance(value, str):
        return None

    value = value.strip()
    return value or None


def _validate_date(value: str | None) -> str | None:
    """Return a normalized ISO date/datetime, or None if invalid."""
    value = _clean_optional_text(value)

    if value is None:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    return parsed.isoformat()


def add_application(
    user_id: str,
    scholarship_id: str,
    status: str,
    notes: str | None = None,
    applied_at: str | None = None,
    scholarship_name: str | None = None,
    provider: str | None = None,
    scholarship_amount: Union[str, float, int, None] = None,
):
    """Create an application record for a scholarship."""
    if not user_id or not scholarship_id:
        return {"error": "User ID and scholarship ID are required"}

    status = status.strip().upper() if isinstance(status, str) else ""

    if status not in VALID_STATUSES:
        return {"error": "Invalid application status"}

    existing = get_application(user_id, scholarship_id)
    if existing:
        return {"error": "Application already exists"}

    if applied_at is not None:
        cleaned_date = _clean_optional_text(applied_at)
        applied_at = _validate_date(applied_at)

        if cleaned_date is not None and applied_at is None:
            return {"error": "Invalid application date. Use an ISO date or datetime."}

    if status in SUBMITTED_STATUSES and applied_at is None:
        applied_at = _now()

    # Look up scholarship details if not provided by caller
    if not scholarship_name:
        stored = get_scholarship(scholarship_id)
        if stored:
            scholarship_name = stored.get("name")
            provider = provider or stored.get("provider")
            scholarship_amount = scholarship_amount or stored.get("scholarship_amount")

    now = _now()

    return create_application({
        "user_id": user_id,
        "scholarship_id": scholarship_id,
        "scholarship_name": _clean_optional_text(scholarship_name),
        "provider": _clean_optional_text(provider),
        "scholarship_amount": scholarship_amount,
        "status": status,
        "notes": _clean_optional_text(notes),
        "applied_at": applied_at,
        "created_at": now,
        "updated_at": now,
    })


def fetch_user_applications(user_id: str):
    """Retrieve all application records belonging to a user."""
    if not user_id:
        return {"error": "User ID is required"}

    return get_user_applications(user_id)


def change_application_status(
    user_id: str,
    scholarship_id: str,
    status: str,
):
    """Update the status of an existing application."""
    if not user_id or not scholarship_id:
        return {"error": "User ID and scholarship ID are required"}

    status = status.strip().upper() if isinstance(status, str) else ""

    if status not in VALID_STATUSES:
        return {"error": "Invalid application status"}

    existing = get_application(user_id, scholarship_id)
    if not existing:
        return {"error": "Application not found"}

    update_data = {
        "status": status,
        "updated_at": _now(),
    }

    if status in SUBMITTED_STATUSES and not existing.get("applied_at"):
        update_data["applied_at"] = _now()

    updated = update_application(
        user_id,
        scholarship_id,
        update_data,
    )

    if not updated:
        return {"error": "Application update failed"}

    return {
        "message": "Application updated",
        "scholarship_id": scholarship_id,
        "status": status,
    }


def update_user_application(
    user_id: str,
    scholarship_id: str,
    status: str | None = None,
    notes: str | None = None,
):
    """Update status and/or notes on an existing application."""
    if not user_id or not scholarship_id:
        return {"error": "User ID and scholarship ID are required"}

    existing = get_application(user_id, scholarship_id)
    if not existing:
        return {"error": "Application not found"}

    update_data = {
        "updated_at": _now(),
    }

    if status is not None:
        status = status.strip().upper() if isinstance(status, str) else ""
        if status not in VALID_STATUSES:
            return {"error": "Invalid application status"}
        update_data["status"] = status
        if status in SUBMITTED_STATUSES and not existing.get("applied_at"):
            update_data["applied_at"] = _now()

    if notes is not None:
        update_data["notes"] = _clean_optional_text(notes)

    updated = update_application(user_id, scholarship_id, update_data)
    if not updated:
        return {"error": "Application update failed"}

    return {
        "message": "Application updated",
        "scholarship_id": scholarship_id,
        "status": update_data.get("status", existing.get("status")),
        "notes": update_data.get("notes", existing.get("notes")),
    }


def remove_application(user_id: str, scholarship_id: str):
    """Delete an application record for the given student."""
    if not user_id or not scholarship_id:
        return {"error": "User ID and scholarship ID are required"}

    deleted = delete_application(user_id, scholarship_id)
    if not deleted:
        return {"error": "Application not found"}

    return {"message": "Application deleted", "scholarship_id": scholarship_id}
