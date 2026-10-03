from fastapi import APIRouter

from app.schemas import ScholarshipCreate
from app.services.scholarship_service import (
    register_scholarship,
    fetch_scholarship,
)


router = APIRouter(
    prefix="/scholarships",
    tags=["Scholarships"]
)


@router.post("/")
def create_scholarship(scholarship: ScholarshipCreate):
    scholarship_data = scholarship.model_dump()

    return register_scholarship(scholarship_data)


@router.get("/{scholarship_id}")
def get_scholarship(scholarship_id: str):
    scholarship = fetch_scholarship(scholarship_id)

    if scholarship is None:
        return {
            "message": "Scholarship not found"
        }

    return scholarship