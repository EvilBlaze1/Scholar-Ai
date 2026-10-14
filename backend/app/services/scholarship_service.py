from app.database.scholarship_repository import (
    create_scholarship,
    get_scholarship,
    get_all_scholarships,
)


def register_scholarship(scholarship_data: dict):
    return create_scholarship(scholarship_data)


def fetch_scholarship(scholarship_id: str):
    return get_scholarship(scholarship_id)


def fetch_all_scholarships(
    category: str | None = None,
    state: str | None = None,
    education_level: str | None = None,
    course: str | None = None,
):
    return get_all_scholarships(
        category=category,
        state=state,
        education_level=education_level,
        course=course,
    )