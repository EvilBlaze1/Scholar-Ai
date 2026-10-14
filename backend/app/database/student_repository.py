from bson import ObjectId
from bson.errors import InvalidId

from app.database.collections import students_collection


def create_student(student_data: dict):
    result = students_collection.insert_one(student_data)

    return {
        "id": str(result.inserted_id)
    }


def get_student(student_id: str):
    try:
        object_id = ObjectId(student_id)
    except InvalidId:
        return None

    student = students_collection.find_one({
        "_id": object_id
    })

    if student is None:
        return None

    student["id"] = str(student["_id"])
    del student["_id"]

    return student


def get_student_by_user_id(user_id: str):
    student = students_collection.find_one({
        "user_id": user_id
    })

    if student is None:
        return None

    student["id"] = str(student["_id"])
    del student["_id"]

    return student


def update_student(student_id: str, student_data: dict):
    try:
        object_id = ObjectId(student_id)
    except InvalidId:
        return None

    result = students_collection.update_one(
        {"_id": object_id},
        {"$set": student_data}
    )

    if result.matched_count == 0:
        return None

    return get_student(student_id)