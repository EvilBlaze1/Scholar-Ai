from fastapi import APIRouter, HTTPException, Query

from app.schemas.search import PersonalizedSearchResponse
from app.services.scholarship_search_service import (
    search_scholarships_for_student,
)

router = APIRouter(
    prefix="/search",
    tags=["Personalized Search"],
)


@router.get(
    "/student/{student_id}",
    response_model=PersonalizedSearchResponse,
)
def personalized_scholarship_search(
    student_id: str,
    refresh: bool = Query(
        False,
        description="Bypass search cache and re-crawl results",
    ),
):
    try:
        result = search_scholarships_for_student(
            student_id,
            force_refresh=refresh,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found",
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Personalized scholarship search failed: {str(error)}",
        )
