from fastapi import APIRouter, HTTPException

from app.services.scholarship_explanation_service import (
    get_scholarship_explanation,
)


router = APIRouter(
    prefix="/explanations",
    tags=["Explanations"]
)


@router.get(
    "/student/{student_id}/scholarship/{scholarship_id}"
)
def explain_scholarship(
    student_id: str,
    scholarship_id: str
):
    result = get_scholarship_explanation(
        student_id,
        scholarship_id
    )

    if result.get("error") == "Student not found":
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    if result.get("error") == "Scholarship not found":
        raise HTTPException(
            status_code=404,
            detail="Scholarship not found"
        )

    return result