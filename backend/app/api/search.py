from fastapi import APIRouter, HTTPException, Query

from app.search.web_search import search_web


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get("/scholarships")
def search_scholarships(
    q: str = Query(..., min_length=2)
):
    try:
        query = f"scholarship {q}"

        results = search_web(query)

        return {
            "query": q,
            "count": len(results),
            "results": results,
        }

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Scholarship search failed: {str(error)}",
        )