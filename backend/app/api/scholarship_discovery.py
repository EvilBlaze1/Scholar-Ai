
import logging

from fastapi import APIRouter, HTTPException, Query

from app.search.web_search import search_web

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/discovery",
    tags=["Scholarship Discovery"],
)


@router.get("/search")
def discover_scholarships(
    q: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="Keywords to find scholarships in India",
    ),
):
    """Search the Internet for scholarship opportunities."""

    query = f"scholarship {q.strip()} India"

    try:
        results = search_web(
            query=query,
            num_results=10,
        )

        if not isinstance(results, list):
            raise RuntimeError("Unexpected search provider response")

        # Remove duplicate URLs while preserving result order.
        unique_results = []
        seen_urls = set()

        for result in results:
            if not isinstance(result, dict):
                continue

            url = result.get("url")

            if not isinstance(url, str) or not url.startswith(
                ("https://", "http://")
            ):
                continue

            normalized_url = url.split("#", 1)[0].rstrip("/").lower()

            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)

            unique_results.append(
                {
                    "title": result.get("title") or "Scholarship opportunity",
                    "url": url,
                    "description": result.get("description") or "",
                }
            )

        logger.info(
            "Scholarship discovery completed: query=%r, results=%d",
            q.strip(),
            len(unique_results),
        )

        return {
            "query": q.strip(),
            "count": len(unique_results),
            "results": unique_results,
        }

    except Exception:
        # Log the full traceback on the backend, without exposing
        # provider details or credentials to the frontend.
        logger.exception(
            "Scholarship discovery failed for query=%r",
            q.strip(),
        )

        raise HTTPException(
            status_code=502,
            detail="Scholarship discovery failed. Please try again.",
        ) from None
