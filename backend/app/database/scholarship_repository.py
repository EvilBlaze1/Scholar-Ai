from bson import ObjectId
from bson.errors import InvalidId

from app.database.collections import scholarships_collection


def create_scholarship(scholarship_data: dict):
    result = scholarships_collection.insert_one(scholarship_data)

    return {
        "id": str(result.inserted_id)
    }


def get_scholarship(scholarship_id: str):
    try:
        object_id = ObjectId(scholarship_id)
    except InvalidId:
        return None

    scholarship = scholarships_collection.find_one(
        {"_id": object_id}
    )

    if scholarship is None:
        return None

    scholarship["id"] = str(scholarship["_id"])
    del scholarship["_id"]

    return scholarship