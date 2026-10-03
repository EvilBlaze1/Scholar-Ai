from fastapi import APIRouter, HTTPException, Path
from app.schemas import EligibilityResult

from app.services.eligibility_service import check_student_eligibility


router = APIRouter(
    prefix="/eligibility",
    tags=["Eligibility"]
)


@router.post(
    "/check/{student_id}/{scholarship_id}",
    response_model=EligibilityResult
)
def check_eligibility(
    student_id: str = Path(..., min_length=24, max_length=24),
    scholarship_id: str = Path(..., min_length=24, max_length=24)
):
    result = check_student_eligibility(
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