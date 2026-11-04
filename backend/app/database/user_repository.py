import logging
import re
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database.collections import users_collection

logger = logging.getLogger(__name__)


def create_user(user_data: dict) -> dict:
    if "email" in user_data and isinstance(user_data["email"], str):
        user_data["email"] = user_data["email"].strip().lower()

    if "created_at" not in user_data:
        user_data["created_at"] = datetime.now(timezone.utc)

    result = users_collection.insert_one(user_data)

    return {
        "id": str(result.inserted_id),
        "email": user_data["email"]
    }


def get_user_by_email(email: str) -> dict | None:
    if not email or not isinstance(email, str):
        return None

    clean_email = email.strip()
    if not clean_email:
        return None

    try:
        # 1. Exact match
        user = users_collection.find_one({"email": clean_email})
        if user:
            return user

        # 2. Lowercase match
        lowered = clean_email.lower()
        if lowered != clean_email:
            user = users_collection.find_one({"email": lowered})
            if user:
                return user

        # 3. Case-insensitive regex match (handles existing users registered with arbitrary casing)
        regex_pattern = f"^{re.escape(clean_email)}$"
        return users_collection.find_one({
            "email": {"$regex": regex_pattern, "$options": "i"}
        })
    except PyMongoError as exc:
        logger.error("Database error in get_user_by_email: %s", exc)
        raise


def get_user_by_id(user_id: str) -> dict | None:
    if not user_id:
        return None

    try:
        if ObjectId.is_valid(user_id):
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return user

        return users_collection.find_one({"_id": str(user_id)})
    except PyMongoError as exc:
        logger.error("Database error in get_user_by_id: %s", exc)
        raise


def update_user_password(user_id: str, new_hash: str) -> bool:
    if not user_id or not new_hash:
        return False

    try:
        query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"_id": str(user_id)}
        res = users_collection.update_one(query, {"$set": {"password_hash": new_hash}})
        return res.modified_count > 0
    except Exception as exc:
        logger.warning("Failed to update user password hash: %s", exc)
        return False
