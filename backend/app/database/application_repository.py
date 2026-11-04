from app.database.collections import applications_collection


def create_application(application_data: dict):
    result = applications_collection.insert_one(
        application_data
    )

    return {
        "id": str(result.inserted_id)
    }


def get_user_applications(user_id: str):
    applications = applications_collection.find({
        "user_id": user_id
    })

    results = []

    for application in applications:
        results.append({
            "id": str(application["_id"]),
            "scholarship_id": application["scholarship_id"],
            "status": application["status"],
            "notes": application.get("notes"),
            "applied_at": application.get("applied_at"),
            "scholarship_name": application.get("scholarship_name"),
            "provider": application.get("provider"),
            "scholarship_amount": application.get("scholarship_amount"),
        })

    return results


def get_application(
    user_id: str,
    scholarship_id: str
):
    return applications_collection.find_one({
        "user_id": user_id,
        "scholarship_id": scholarship_id
    })


def update_application(
    user_id: str,
    scholarship_id: str,
    update_data: dict
):
    result = applications_collection.update_one(
        {
            "user_id": user_id,
            "scholarship_id": scholarship_id
        },
        {
            "$set": update_data
        }
    )

    return result.matched_count > 0


def delete_application(
    user_id: str,
    scholarship_id: str,
) -> bool:
    user_id = str(user_id).strip()
    scholarship_id = str(scholarship_id).strip()

    result = applications_collection.delete_one({
        "user_id": user_id,
        "scholarship_id": scholarship_id,
    })

    if result.deleted_count > 0:
        return True

    from bson import ObjectId
    if ObjectId.is_valid(scholarship_id):
        try:
            res_oid = applications_collection.delete_one({
                "user_id": user_id,
                "_id": ObjectId(scholarship_id),
            })
            if res_oid.deleted_count > 0:
                return True
        except Exception:
            pass

    return False
