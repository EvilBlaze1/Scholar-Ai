from app.database.scholarship_repository import (
    create_scholarship,
    get_scholarship,
)


def register_scholarship(scholarship_data: dict):
    return create_scholarship(scholarship_data)


def fetch_scholarship(scholarship_id: str):
    return get_scholarship(scholarship_id)