
from datetime import datetime, timezone
from bson import ObjectId

from app.database.collections import saved_scholarships_collection


def save_scholarship(
    user_id: str,
    scholarship_id: str,
    scholarship_data: dict | None = None,
):
    """
    Save a scholarship once per user, preventing duplicates.
    """
    if not user_id or not scholarship_id:
        raise ValueError("User ID and scholarship ID are required.")

    user_id = str(user_id).strip()
    scholarship_id = str(scholarship_id).strip()

    # Build match criteria to prevent duplicate saves across multiple ID formats
    or_clauses = [
        {"scholarship_id": scholarship_id},
        {"scholarship_data.id": scholarship_id},
    ]

    source_url = None
    if isinstance(scholarship_data, dict):
        source_url = scholarship_data.get("source_url") or scholarship_data.get("url")
        if source_url:
            source_url = str(source_url).strip()
            or_clauses.append({"scholarship_id": source_url})
            or_clauses.append({"scholarship_data.source_url": source_url})

    existing = saved_scholarships_collection.find_one({
        "user_id": user_id,
        "$or": or_clauses,
    })

    if existing:
        return {
            "id": str(existing["_id"]),
            "user_id": user_id,
            "scholarship_id": existing.get("scholarship_id", scholarship_id),
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
    user_id = str(user_id).strip()
    saved = saved_scholarships_collection.find({
        "user_id": user_id,
    }).sort("saved_at", -1)

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
            record["saved_at"] = (
                item["saved_at"].isoformat()
                if hasattr(item["saved_at"], "isoformat")
                else str(item["saved_at"])
            )

        results.append(record)

    return results


def delete_saved_scholarship(
    user_id: str,
    scholarship_id: str,
):
    """
    Remove a saved scholarship belonging to the specified user.
    Supports deleting by scholarship_id, source_url, or document _id.
    """
    if not user_id or not scholarship_id:
        return False

    user_id = str(user_id).strip()
    scholarship_id = str(scholarship_id).strip()

    # 1. Try deleting by scholarship_id, snapshot id, or source_url
    result = saved_scholarships_collection.delete_one({
        "user_id": user_id,
        "$or": [
            {"scholarship_id": scholarship_id},
            {"scholarship_data.id": scholarship_id},
            {"scholarship_data.source_url": scholarship_id},
            {"scholarship_data.scholarship_id": scholarship_id},
        ],
    })

    if result.deleted_count > 0:
        return True

    # 2. Try deleting by MongoDB ObjectId _id
    if ObjectId.is_valid(scholarship_id):
        try:
            result_oid = saved_scholarships_collection.delete_one({
                "user_id": user_id,
                "_id": ObjectId(scholarship_id),
            })
            if result_oid.deleted_count > 0:
                return True
        except Exception:
            pass

    return False
