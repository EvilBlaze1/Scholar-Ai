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
            "applied_at": application.get("applied_at")
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