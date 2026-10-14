from fastapi import APIRouter, HTTPException

from app.services.matching_service import find_matching_scholarships


router = APIRouter(
    prefix="/matching",
    tags=["Matching"]
)


@router.get("/student/{student_id}")
def get_matching_scholarships(student_id: str):
    matches = find_matching_scholarships(student_id)

    if matches is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "student_id": student_id,
        "total": len(matches),
        "matches": matches
    }