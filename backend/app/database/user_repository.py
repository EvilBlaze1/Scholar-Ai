from app.database.collections import users_collection


def create_user(user_data: dict):
    result = users_collection.insert_one(user_data)

    return {
        "id": str(result.inserted_id),
        "email": user_data["email"]
    }


def get_user_by_email(email: str):
    return users_collection.find_one({
        "email": email
    })