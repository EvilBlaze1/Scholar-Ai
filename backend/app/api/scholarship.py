from fastapi import APIRouter

from app.schemas import ScholarshipCreate
from app.services.scholarship_service import (
    register_scholarship,
    fetch_scholarship,
    fetch_all_scholarships,
)


router = APIRouter(
    prefix="/scholarships",
    tags=["Scholarships"]
)


@router.post("/")
def create_scholarship(scholarship: ScholarshipCreate):
    scholarship_data = scholarship.model_dump()

    return register_scholarship(scholarship_data)


@router.get("/")
def get_scholarships(
    category: str | None = None,
    state: str | None = None,
    education_level: str | None = None,
    course: str | None = None,
):
    return fetch_all_scholarships(
        category=category,
        state=state,
        education_level=education_level,
        course=course,
    )


@router.get("/{scholarship_id}")
def get_scholarship(scholarship_id: str):
    scholarship = fetch_scholarship(scholarship_id)

    if scholarship is None:
        return {
            "message": "Scholarship not found"
        }

    return scholarship