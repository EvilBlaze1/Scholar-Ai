import logging
from urllib.parse import urlsplit, urlunsplit

from app.core.search_cache import (
    get_cached_search,
    make_cache_key,
    set_cached_search,
)
from app.database.student_repository import get_student
from app.search.web_search import search_web
from app.services.scholarship_extraction_service import (
    extract_from_search_results,
)
from app.services.web_scholarship_converter import (
    convert_web_scholarship_to_schema,
)
from app.services.web_eligibility_service import (
    evaluate_web_scholarship,
)

logger = logging.getLogger(__name__)

MAX_QUERIES = 6
RESULTS_PER_QUERY = 5
MAX_UNIQUE_PAGES = 20

STATUS_PRIORITY = {
    "ELIGIBLE": 3,
    "NEEDS_VERIFICATION": 2,
    "INELIGIBLE": 1,
}


def build_search_queries(student: dict) -> list[str]:
    """Build personalized scholarship searches for an Indian student."""

    queries = []

    course = student.get("course")
    specialization = student.get("specialization")
    state = student.get("state") or student.get("domicile_state")
    category = student.get("category")
    education_level = student.get("education_level")
    gender = student.get("gender")

    def add_query(*parts):
        query = " ".join(
            str(part).strip()
            for part in parts
            if part and str(part).strip()
        )

        if query and query.lower() not in {
            existing.lower() for existing in queries
        }:
            queries.append(query)

    if course and state:
        add_query(course, "scholarships", state, "India")

    if course and category:
        add_query(course, category, "scholarships India")

    if specialization:
        add_query(specialization, "scholarships students India")

    if education_level and course:
        add_query(education_level, course, "scholarships India")

    if gender and str(gender).upper() in {
        "FEMALE",
        "GIRL",
        "WOMAN",
    }:
        add_query("women girls scholarships", course, "India")

    if course:
        add_query(course, "scholarships India")

    if state:
        add_query("state government scholarships", state, "students")

    if category:
        add_query(category, "scholarships students India")

    add_query("government scholarships college students India")
    add_query("private foundation merit scholarships students India")

    return queries


def calculate_match_score(eligibility: dict) -> float:
    """
    Calculate a provisional rule-match score.

    This is not a probability of receiving a scholarship.
    Unknown rules are not treated as passed rules.
    """

    passed = eligibility.get("passed_rules", 0)
    failed = eligibility.get("failed_rules", 0)

    if not isinstance(passed, (int, float)):
        passed = 0

    if not isinstance(failed, (int, float)):
        failed = 0

    total = passed + failed

    if total <= 0:
        return 0.0

    return round((passed / total) * 100, 2)


def normalize_url(url: str) -> str | None:
    """Normalize a URL for deduplication without changing its destination."""

    if not isinstance(url, str) or not url.strip():
        return None

    try:
        parts = urlsplit(url.strip())

        if parts.scheme.lower() not in {"http", "https"}:
            return None

        if not parts.hostname:
            return None

        # Remove common tracking parameters.
        tracking_prefixes = ("utm_",)
        tracking_names = {
            "gclid",
            "fbclid",
            "ref",
            "source",
        }

        query_parts = []

        for parameter in parts.query.split("&"):
            if not parameter:
                continue

            key = parameter.split("=", 1)[0].lower()

            if key in tracking_names or key.startswith(tracking_prefixes):
                continue

            query_parts.append(parameter)

        query = "&".join(query_parts)

        path = parts.path.rstrip("/") or "/"

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            query,
            "",
        ))

    except (ValueError, TypeError):
        return None


def search_scholarships_for_student(student_id: str, force_refresh: bool = False):
    """Discover, extract, and evaluate scholarships for one student."""

    student = get_student(student_id)

    if student is None:
        return None

    # Check cache first unless force_refresh is requested
    cache_key = make_cache_key(
        "student_search",
        student_id,
        student.get("course"),
        student.get("specialization"),
        student.get("state") or student.get("domicile_state"),
        student.get("category"),
        student.get("education_level"),
        student.get("gender"),
        student.get("annual_family_income"),
        student.get("score"),
        student.get("score_type"),
    )

    if not force_refresh:
        cached = get_cached_search("student_search", cache_key)
        if cached is not None and isinstance(cached, dict):
            logger.info("Serving personalized search from cache for student_id=%s", student_id)
            cached["cached"] = True
            return cached

    queries = build_search_queries(student)
    selected_queries = queries[:MAX_QUERIES]

    unique_results = {}
    search_errors = []

    for query in selected_queries:
        try:
            results = search_web(
                query,
                num_results=RESULTS_PER_QUERY,
                use_cache=not force_refresh,
            )

            if not isinstance(results, list):
                continue

            for result in results:
                if not isinstance(result, dict):
                    continue

                original_url = result.get("url")
                normalized_url = normalize_url(original_url)

                if not normalized_url:
                    continue

                if normalized_url not in unique_results:
                    unique_results[normalized_url] = {
                        **result,
                        "url": original_url,
                        "search_query": query,
                    }

        except Exception:
            # One failed query should not cancel the other searches.
            search_errors.append(query)
            continue

    raw_results = list(unique_results.values())[:MAX_UNIQUE_PAGES]

    if not raw_results:
        return {
            "student_id": student_id,
            "queries": selected_queries,
            "count": 0,
            "results": [],
            "search_errors": len(search_errors),
            "cached": False,
            "message": (
                "Search providers did not return usable results. "
                "Please try again later."
            ),
        }

    try:
        extracted_scholarships = extract_from_search_results(raw_results)
    except Exception:
        extracted_scholarships = []

    evaluated_scholarships = []
    seen_scholarships = set()

    for extracted in extracted_scholarships or []:
        if not isinstance(extracted, dict):
            continue

        source_url = (
            extracted.get("source_url")
            or extracted.get("url")
        )

        normalized_source = normalize_url(source_url)

        if normalized_source and normalized_source in seen_scholarships:
            continue

        if normalized_source:
            seen_scholarships.add(normalized_source)

        try:
            scholarship = convert_web_scholarship_to_schema(extracted)

            if not isinstance(scholarship, dict):
                continue

            evaluation = evaluate_web_scholarship(
                student,
                scholarship,
            )

            eligibility = (
                evaluation.get("eligibility", {})
                if isinstance(evaluation, dict)
                else {}
            )

            if not isinstance(eligibility, dict):
                eligibility = {}

            status = eligibility.get(
                "status",
                "NEEDS_VERIFICATION",
            )

            verification_required = eligibility.get(
                "verification_required",
                True,
            )

            # Never label an unverified record as eligible solely because
            # the evaluator omitted its verification status.
            if verification_required and status == "ELIGIBLE":
                status = "NEEDS_VERIFICATION"

            evaluated_scholarships.append({
                **scholarship,
                "source_url": (
                    scholarship.get("source_url")
                    or source_url
                ),
                "eligibility_status": status,
                "passed_rules": eligibility.get("passed_rules", 0),
                "failed_rules": eligibility.get("failed_rules", 0),
                "verification_required": verification_required,
                "match_score": calculate_match_score(eligibility),
            })

        except Exception:
            # Skip malformed records rather than failing the entire search.
            continue

    evaluated_scholarships.sort(
        key=lambda item: (
            STATUS_PRIORITY.get(
                item.get("eligibility_status"),
                0,
            ),
            item.get("match_score", 0),
        ),
        reverse=True,
    )

    output = {
        "student_id": student_id,
        "queries": selected_queries,
        "count": len(evaluated_scholarships),
        "results": evaluated_scholarships,
        "search_errors": len(search_errors),
        "cached": False,
    }

    # Cache evaluated results for 30 minutes (1800s) if we found results
    if evaluated_scholarships:
        set_cached_search("student_search", cache_key, output, ttl_seconds=1800)

    return output
