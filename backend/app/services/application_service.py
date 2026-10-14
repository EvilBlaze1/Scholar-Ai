
from datetime import datetime, timezone

from app.database.application_repository import (
    create_application,
    get_user_applications,
    get_application,
    update_application,
)


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

    now = _now()

    return create_application({
        "user_id": user_id,
        "scholarship_id": scholarship_id,
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

    # Record the first application date when the student moves
    # into a submitted or post-submission status.
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
