
from app.database.saved_scholarship_repository import (
    save_scholarship,
    get_saved_scholarships,
    delete_saved_scholarship,
)


def add_saved_scholarship(
    user_id: str,
    scholarship_id: str,
    scholarship_data: dict | None = None,
):
    """Save a scholarship, optionally retaining its discovered details."""
    return save_scholarship(
        user_id,
        scholarship_id,
        scholarship_data,
    )


def fetch_saved_scholarships(user_id: str):
    """Return the scholarships saved by a user."""
    return get_saved_scholarships(user_id)


def remove_saved_scholarship(
    user_id: str,
    scholarship_id: str,
):
    """Remove a scholarship from a user's saved list."""
    return delete_saved_scholarship(
        user_id,
        scholarship_id,
    )
