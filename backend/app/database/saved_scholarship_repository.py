
from datetime import datetime, timezone

from app.database.collections import saved_scholarships_collection


def save_scholarship(
    user_id: str,
    scholarship_id: str,
    scholarship_data: dict | None = None,
):
    """
    Save a scholarship once per user.

    scholarship_data is optional so existing callers that pass only
    user_id and scholarship_id remain compatible.
    """
    if not user_id or not scholarship_id:
        raise ValueError("User ID and scholarship ID are required.")

    existing = saved_scholarships_collection.find_one({
        "user_id": user_id,
        "scholarship_id": scholarship_id,
    })

    if existing:
        return {
            "id": str(existing["_id"]),
            "user_id": user_id,
            "scholarship_id": scholarship_id,
            "already_saved": True,
        }

    document = {
        "user_id": user_id,
        "scholarship_id": scholarship_id,
        "scholarship_data": scholarship_data,
        "saved_at": datetime.now(timezone.utc),
    }

    result = saved_scholarships_collection.insert_one(document)

    return {
        "id": str(result.inserted_id),
        "user_id": user_id,
        "scholarship_id": scholarship_id,
        "already_saved": False,
    }


def get_saved_scholarships(user_id: str):
    """Return saved scholarship IDs and any stored scholarship snapshots."""
    saved = saved_scholarships_collection.find({
        "user_id": user_id,
    })

    results = []

    for item in saved:
        record = {
            "id": str(item["_id"]),
            "scholarship_id": item.get("scholarship_id"),
        }

        scholarship_data = item.get("scholarship_data")

        if isinstance(scholarship_data, dict):
            record["scholarship"] = scholarship_data

        if item.get("saved_at"):
            record["saved_at"] = item["saved_at"].isoformat()

        results.append(record)

    return results


def delete_saved_scholarship(
    user_id: str,
    scholarship_id: str,
):
    """Remove a saved scholarship belonging to the specified user."""
    result = saved_scholarships_collection.delete_one({
        "user_id": user_id,
        "scholarship_id": scholarship_id,
    })

    return result.deleted_count > 0
